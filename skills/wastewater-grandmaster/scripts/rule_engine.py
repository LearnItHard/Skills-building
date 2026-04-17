"""
Typed rule engine for evaluating wastewater design parameters against
mandatory clauses and design rules from GB 50014-2021.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

try:
    from .common.citation import make_citation, resolve_reference_relative_path
except ImportError:
    from common.citation import make_citation, resolve_reference_relative_path


class RuleResultStatus(Enum):
    PASS = "PASS"
    VIOLATION = "VIOLATION"
    WARNING = "WARNING"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class RuleResult:
    clause: str
    text: str
    type: str
    rule_type: str
    domain: str
    status: RuleResultStatus
    severity: str
    source_file: str
    citation_text: str
    message: str


class TypedRuleEngine:
    """
    Loads mandatory clauses and design rules from JSON files and evaluates
    design parameters against them.
    """

    def __init__(self, mandatory_path: str, design_path: str):
        self.mandatory_path = mandatory_path
        self.design_path = design_path

        with open(mandatory_path, "r", encoding="utf-8") as f:
            self.mandatory_clauses = json.load(f)

        with open(design_path, "r", encoding="utf-8") as f:
            self.design_rules = json.load(f)

        # Combine into a single lookup for convenience.
        self.all_rules = [dict(rule) for rule in self.mandatory_clauses]
        self.all_rules.extend(dict(rule) for rule in self.design_rules)

    def list_domains(self) -> list[str]:
        """Return the distinct rule domains available in the loaded datasets."""
        return sorted({rule.get("domain", "") for rule in self.all_rules if rule.get("domain")})

    def check(
        self,
        domain: str,
        design_context: dict[str, Any],
        parameters: dict[str, Any],
    ) -> list[RuleResult]:
        """
        Evaluate all rules matching the given domain against the provided
        design context and parameters.
        """
        results: list[RuleResult] = []

        for rule in self.all_rules:
            if rule.get("domain") != domain:
                continue

            result = self._evaluate_rule(rule, design_context, parameters)
            results.append(result)

        return results

    def _evaluate_rule(
        self,
        rule: dict[str, Any],
        design_context: dict[str, Any],
        parameters: dict[str, Any],
    ) -> RuleResult:
        clause = rule.get("clause", "")
        text = rule.get("text", "")
        rule_type = rule.get("rule_type", "")
        domain = rule.get("domain", "")
        severity = rule.get("severity", "")
        source_file_hint = rule.get("source_file")
        source_file = resolve_reference_relative_path(clause, source_file_hint)
        rule_type_field = rule.get("type", "")
        condition = rule.get("condition", "")

        citation_text = make_citation(clause, source_file_hint)

        # Check applicability based on system_type
        system_type = design_context.get("system_type", "")
        if system_type and not self._is_applicable(rule, system_type):
            return RuleResult(
                clause=clause,
                text=text,
                type=rule_type_field,
                rule_type=rule_type,
                domain=domain,
                status=RuleResultStatus.NOT_APPLICABLE,
                severity=severity,
                source_file=source_file,
                citation_text=citation_text,
                message=f"Rule does not apply to system_type '{system_type}'.",
            )

        # Dispatch by rule_type
        handler = getattr(self, f"_handle_{rule_type}", None)
        if handler is None:
            return RuleResult(
                clause=clause,
                text=text,
                type=rule_type_field,
                rule_type=rule_type,
                domain=domain,
                status=RuleResultStatus.MANUAL_REVIEW,
                severity=severity,
                source_file=source_file,
                citation_text=citation_text,
                message=f"Unknown rule_type '{rule_type}'; manual review required.",
            )

        status, message = handler(rule, condition, design_context, parameters)
        return RuleResult(
            clause=clause,
            text=text,
            type=rule_type_field,
            rule_type=rule_type,
            domain=domain,
            status=status,
            severity=severity,
            source_file=source_file,
            citation_text=citation_text,
            message=message,
        )

    def _is_applicable(self, rule: dict[str, Any], system_type: str) -> bool:
        """
        Determine whether a rule applies to the given system_type.
        """
        domain = rule.get("domain", "")
        text = rule.get("text", "")

        system_type = system_type.lower()

        # Explicit domain-based exclusions
        storm_only_domains = {"stormwater_design"}
        sewage_only_domains = {
            "wastewater_collection",
            "sewer_appurtenances",
            "wastewater_treatment",
            "sludge_treatment",
            "reclaimed_water",
            "natural_treatment",
        }

        if system_type == "storm":
            if domain in sewage_only_domains:
                return False
            # Heuristic: if text explicitly refers to sewage-only features
            # and does not mention stormwater, it may not apply
            if "污水" in text and "雨水" not in text and "合流" not in text:
                if any(kw in text for kw in ("污水管道", "重力流污水", "水封井", "化粪池")):
                    return False

        if system_type == "sewage":
            if domain in storm_only_domains:
                return False

        if system_type == "combined":
            # Combined systems are broadly applicable; only exclude very specific ones
            pass

        return True

    def _violation_status(self, rule: dict[str, Any]) -> RuleResultStatus:
        severity = rule.get("severity", "")
        if severity in ("mandatory", "shall"):
            return RuleResultStatus.VIOLATION
        return RuleResultStatus.WARNING

    def _handle_numeric_threshold(
        self,
        rule: dict[str, Any],
        condition: Any,
        design_context: dict[str, Any],
        parameters: dict[str, Any],
    ) -> tuple[RuleResultStatus, str]:
        if not isinstance(condition, dict):
            return (
                RuleResultStatus.MANUAL_REVIEW,
                "Numeric threshold rule lacks a structured condition; manual review required.",
            )

        # Handle nested structures (e.g., pressure_test_multiplier inside condition)
        # If condition does not have parameter/operator directly, look for nested dicts
        flat_conditions = self._flatten_numeric_conditions(condition)
        if not flat_conditions:
            return (
                RuleResultStatus.MANUAL_REVIEW,
                "Numeric threshold rule condition could not be parsed; manual review required.",
            )

        violations = []
        for cond in flat_conditions:
            param_name = cond.get("parameter")
            operator = cond.get("operator")
            reference = cond.get("reference")
            value = cond.get("value")

            if not param_name or not operator:
                continue

            if param_name not in parameters:
                return (
                    RuleResultStatus.MANUAL_REVIEW,
                    f"Required parameter '{param_name}' not provided; manual review required.",
                )

            actual_value = parameters[param_name]
            try:
                actual_value = float(actual_value)
            except (TypeError, ValueError):
                return (
                    RuleResultStatus.MANUAL_REVIEW,
                    f"Parameter '{param_name}' is not numeric; manual review required.",
                )

            if reference is not None:
                if reference not in parameters:
                    return (
                        RuleResultStatus.MANUAL_REVIEW,
                        f"Reference parameter '{reference}' not provided; manual review required.",
                    )
                compare_value = parameters[reference]
                try:
                    compare_value = float(compare_value)
                except (TypeError, ValueError):
                    return (
                        RuleResultStatus.MANUAL_REVIEW,
                        f"Reference parameter '{reference}' is not numeric; manual review required.",
                    )
            elif value is not None:
                try:
                    compare_value = float(value)
                except (TypeError, ValueError):
                    return (
                        RuleResultStatus.MANUAL_REVIEW,
                        f"Comparison value '{value}' is not numeric; manual review required.",
                    )
            else:
                return (
                    RuleResultStatus.MANUAL_REVIEW,
                    "Numeric threshold rule missing both 'value' and 'reference'; manual review required.",
                )

            if not self._compare(actual_value, operator, compare_value):
                violations.append(
                    f"{param_name} = {actual_value} does not satisfy {operator} {compare_value}"
                )

        if violations:
            return self._violation_status(rule), "; ".join(violations)

        return RuleResultStatus.PASS, "All numeric thresholds satisfied."

    def _flatten_numeric_conditions(
        self, condition: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Flatten a potentially nested condition dict into a list of simple
        {parameter, operator, value/reference} dicts.
        """
        # Direct simple condition
        if "parameter" in condition and "operator" in condition:
            return [condition]

        results = []
        for key, val in condition.items():
            if isinstance(val, dict) and "operator" in val:
                # Nested condition like pressure_test_multiplier
                sub = dict(val)
                if "parameter" not in sub:
                    # Derive parameter from key name if sensible
                    sub["parameter"] = key
                results.append(sub)
            elif key in ("context",) and isinstance(val, str):
                # Context metadata, ignore
                continue
        return results

    def _compare(self, left: float, operator: str, right: float) -> bool:
        if operator == "<=":
            return left <= right
        if operator == "<":
            return left < right
        if operator == ">=":
            return left >= right
        if operator == ">":
            return left > right
        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        raise ValueError(f"Unsupported operator: {operator}")

    def _handle_enum_branch(
        self,
        rule: dict[str, Any],
        condition: Any,
        design_context: dict[str, Any],
        parameters: dict[str, Any],
    ) -> tuple[RuleResultStatus, str]:
        if not isinstance(condition, dict):
            return (
                RuleResultStatus.MANUAL_REVIEW,
                "Enum branch rule lacks a structured condition; manual review required.",
            )

        mismatches = []
        for key, expected in condition.items():
            actual = design_context.get(key)
            if actual is None and key not in design_context:
                actual = parameters.get(key)

            if expected is True and not actual:
                mismatches.append(f"'{key}' expected to be true, got {actual}")
            elif expected is False and actual:
                mismatches.append(f"'{key}' expected to be false, got {actual}")
            elif isinstance(expected, str) and str(actual) != expected:
                mismatches.append(f"'{key}' expected '{expected}', got '{actual}'")

        if mismatches:
            return self._violation_status(rule), "; ".join(mismatches)

        return RuleResultStatus.PASS, "All enum branch conditions satisfied."

    def _handle_facility_existence(
        self,
        rule: dict[str, Any],
        condition: Any,
        design_context: dict[str, Any],
        parameters: dict[str, Any],
    ) -> tuple[RuleResultStatus, str]:
        if not isinstance(condition, dict):
            return (
                RuleResultStatus.MANUAL_REVIEW,
                "Facility existence rule lacks a structured condition; manual review required.",
            )

        # If there's a trigger, only enforce when trigger is active
        trigger = condition.get("trigger")
        if trigger is not None:
            if not parameters.get(trigger) and not design_context.get(trigger):
                return (
                    RuleResultStatus.PASS,
                    f"Trigger '{trigger}' is not active; facility requirement does not apply.",
                )

        missing = []

        required_facility = condition.get("required_facility")
        if required_facility is not None:
            exists = parameters.get(f"has_{required_facility}", False) or parameters.get(
                required_facility, False
            )
            if not exists:
                missing.append(required_facility)

        required_facilities = condition.get("required_facilities")
        if isinstance(required_facilities, list):
            for facility in required_facilities:
                exists = parameters.get(f"has_{facility}", False) or parameters.get(
                    facility, False
                )
                if not exists:
                    missing.append(facility)

        # Handle flat boolean keys like "water_seal_device": "required"
        for key, val in condition.items():
            if key in ("trigger", "required_facility", "required_facilities", "location"):
                continue
            if val == "required":
                exists = parameters.get(f"has_{key}", False) or parameters.get(key, False)
                if not exists:
                    missing.append(key)

        if missing:
            return self._violation_status(rule), f"Missing required facilities: {', '.join(missing)}"

        return RuleResultStatus.PASS, "All required facilities present."

    def _handle_manual_review(
        self,
        rule: dict[str, Any],
        condition: Any,
        design_context: dict[str, Any],
        parameters: dict[str, Any],
    ) -> tuple[RuleResultStatus, str]:
        return (
            RuleResultStatus.MANUAL_REVIEW,
            "This rule requires manual review by a qualified engineer.",
        )
