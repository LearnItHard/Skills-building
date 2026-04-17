"""Comprehensive tests for the TypedRuleEngine."""

import importlib
import json
import os
import sys
import tempfile

import pytest

# Ensure scripts directory is on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from rule_engine import RuleResultStatus, TypedRuleEngine
from common.citation import resolve_reference_relative_path

MANDATORY_PATH = os.path.join(REPO_ROOT, "references", "mandatory_clauses.json")
DESIGN_PATH = os.path.join(REPO_ROOT, "references", "design_rules.json")


@pytest.fixture
def engine():
    return TypedRuleEngine(MANDATORY_PATH, DESIGN_PATH)


class TestTypedRuleEngineBasics:
    def test_package_style_import_works(self):
        module = importlib.import_module("scripts.rule_engine")
        assert hasattr(module, "TypedRuleEngine")

    def test_loads_both_json_files(self, engine):
        assert len(engine.mandatory_clauses) == 14
        assert len(engine.design_rules) > 2000
        assert len(engine.all_rules) == 14 + len(engine.design_rules)

    def test_list_domains(self, engine):
        domains = engine.list_domains()
        assert "stormwater_design" in domains
        assert "排水管渠和附属构筑物" in domains

    def test_check_filters_by_domain(self, engine):
        results = engine.check("stormwater_design", {"system_type": "storm"}, {})
        assert len(results) >= 1
        for r in results:
            assert r.domain == "stormwater_design"

    def test_all_results_have_citation_text(self, engine):
        results = engine.check("stormwater_design", {"system_type": "storm"}, {})
        for r in results:
            assert r.citation_text.startswith("GB 50014-2021")
            assert r.clause in r.citation_text

    def test_resolved_source_file_points_to_real_reference(self, engine):
        results = engine.check(
            "stormwater_design",
            {"system_type": "storm"},
            {"post_dev_runoff": 80.0, "pre_dev_runoff": 100.0},
        )
        target = [r for r in results if r.clause == "4.1.6"][0]
        assert target.source_file.startswith("references/gb50014-2021/")
        resolved_path = os.path.join(REPO_ROOT, target.source_file.replace("/", os.sep))
        assert os.path.exists(resolved_path)

    def test_citation_helper_resolves_real_nested_path(self):
        relative_path = resolve_reference_relative_path("4.1.7")
        assert relative_path.startswith("references/gb50014-2021/53-416")
        resolved_path = os.path.join(REPO_ROOT, relative_path.replace("/", os.sep))
        assert os.path.exists(resolved_path)


class TestMandatoryClauseViolations:
    def test_legal_mandatory_4_1_6_runoff_violation(self, engine):
        """
        Clause 4.1.6: post-development runoff must not exceed pre-development runoff.
        """
        results = engine.check(
            "stormwater_design",
            {"system_type": "storm"},
            {"post_dev_runoff": 120.0, "pre_dev_runoff": 100.0},
        )
        rule_results = [r for r in results if r.clause == "4.1.6"]
        assert len(rule_results) == 1
        result = rule_results[0]
        assert result.status == RuleResultStatus.VIOLATION
        assert "post_dev_runoff" in result.message

    def test_legal_mandatory_4_1_6_runoff_pass(self, engine):
        results = engine.check(
            "stormwater_design",
            {"system_type": "storm"},
            {"post_dev_runoff": 80.0, "pre_dev_runoff": 100.0},
        )
        rule_results = [r for r in results if r.clause == "4.1.6"]
        assert len(rule_results) == 1
        result = rule_results[0]
        assert result.status == RuleResultStatus.PASS


class TestDesignRuleEvaluations:
    def test_design_rule_fullness_violation(self, engine):
        """
        Simulate a design rule violation: fullness > 0.55 for a 250 mm sewage pipe.
        We inject a synthetic structured rule to exercise numeric_threshold logic.
        """
        synthetic_rule = {
            "clause": "5.2.4-test",
            "text": "重力流污水管道最大设计充满度不应超过0.55（管径250mm）。",
            "type": "design_rule",
            "rule_type": "numeric_threshold",
            "domain": "sewer_hydraulics",
            "condition": {
                "parameter": "fullness",
                "operator": "<=",
                "value": 0.55,
            },
            "severity": "shall",
            "source": "GB 50014-2021 室外排水设计标准",
        }
        engine.all_rules.append(synthetic_rule)

        results = engine.check(
            "sewer_hydraulics",
            {"system_type": "sewage"},
            {"fullness": 0.60, "pipe_diameter_mm": 250},
        )
        target = [r for r in results if r.clause == "5.2.4-test"][0]
        assert target.status == RuleResultStatus.VIOLATION
        assert "0.6" in target.message or "0.60" in target.message
        assert "0.55" in target.message
        assert target.citation_text.startswith("GB 50014-2021")

    def test_design_rule_fullness_pass(self, engine):
        synthetic_rule = {
            "clause": "5.2.4-test-pass",
            "text": "重力流污水管道最大设计充满度不应超过0.55（管径250mm）。",
            "type": "design_rule",
            "rule_type": "numeric_threshold",
            "domain": "sewer_hydraulics",
            "condition": {
                "parameter": "fullness",
                "operator": "<=",
                "value": 0.55,
            },
            "severity": "shall",
            "source": "GB 50014-2021 室外排水设计标准",
        }
        engine.all_rules.append(synthetic_rule)

        results = engine.check(
            "sewer_hydraulics",
            {"system_type": "sewage"},
            {"fullness": 0.50, "pipe_diameter_mm": 250},
        )
        target = [r for r in results if r.clause == "5.2.4-test-pass"][0]
        assert target.status == RuleResultStatus.PASS


class TestManualReview:
    def test_manual_review_prompt(self, engine):
        """
        Any manual_review rule should always return MANUAL_REVIEW.
        """
        # Use a real manual_review rule from design_rules.json
        results = engine.check(
            "总则",
            {"system_type": "sewage"},
            {},
        )
        manual_results = [r for r in results if r.rule_type == "manual_review"]
        assert len(manual_results) >= 1
        for r in manual_results:
            assert r.status == RuleResultStatus.MANUAL_REVIEW
            assert "manual review" in r.message.lower() or "手动" in r.message or "人工" in r.message or "manual_review" in r.message.lower()

    def test_unknown_rule_type_defaults_to_manual_review(self, engine):
        synthetic_rule = {
            "clause": "99.9.9",
            "text": "Unknown rule type test.",
            "type": "design_rule",
            "rule_type": "future_magic_type",
            "domain": "test_domain",
            "condition": {},
            "severity": "shall",
        }
        engine.all_rules.append(synthetic_rule)

        results = engine.check("test_domain", {"system_type": "sewage"}, {})
        target = [r for r in results if r.clause == "99.9.9"][0]
        assert target.status == RuleResultStatus.MANUAL_REVIEW
        assert "Unknown rule_type" in target.message


class TestNotApplicable:
    def test_sewage_fullness_rule_on_storm_system(self, engine):
        """
        Sewage-specific rules should be NOT_APPLICABLE when checked against a storm system.
        We use the real 5.2.4 design rule from design_rules.json.
        """
        results = engine.check(
            "排水管渠和附属构筑物",
            {"system_type": "storm"},
            {},
        )
        # Find the 5.2.4 rule that explicitly mentions gravity-flow sewage pipes
        target = None
        for r in results:
            if r.clause == "5.2.4" and "重力流污水管道" in r.text:
                target = r
                break

        assert target is not None, "Expected to find rule 5.2.4 about gravity sewage pipes"
        assert target.status == RuleResultStatus.NOT_APPLICABLE
        assert "storm" in target.message

    def test_storm_rule_on_sewage_system(self, engine):
        """
        Storm-specific mandatory clause should be NOT_APPLICABLE for sewage system.
        """
        results = engine.check(
            "stormwater_design",
            {"system_type": "sewage"},
            {},
        )
        target = [r for r in results if r.clause == "4.1.6"][0]
        assert target.status == RuleResultStatus.NOT_APPLICABLE


class TestFacilityExistence:
    def test_facility_existence_trigger_not_active_passes(self, engine):
        """
        Clause 5.6.1: water seal well is required only when industrial wastewater
        produces explosive/flammable gas.
        """
        results = engine.check(
            "sewer_appurtenances",
            {"system_type": "sewage"},
            {"industrial_wastewater_produces_explosive_or_flammable_gas": False},
        )
        target = [r for r in results if r.clause == "5.6.1"][0]
        assert target.status == RuleResultStatus.PASS
        assert "not active" in target.message or "does not apply" in target.message

    def test_facility_existence_trigger_active_missing_facility(self, engine):
        results = engine.check(
            "sewer_appurtenances",
            {"system_type": "sewage"},
            {
                "industrial_wastewater_produces_explosive_or_flammable_gas": True,
                "has_water_seal_well": False,
            },
        )
        target = [r for r in results if r.clause == "5.6.1"][0]
        assert target.status == RuleResultStatus.VIOLATION
        assert "water_seal_well" in target.message

    def test_facility_existence_trigger_active_has_facility(self, engine):
        results = engine.check(
            "sewer_appurtenances",
            {"system_type": "sewage"},
            {
                "industrial_wastewater_produces_explosive_or_flammable_gas": True,
                "has_water_seal_well": True,
            },
        )
        target = [r for r in results if r.clause == "5.6.1"][0]
        assert target.status == RuleResultStatus.PASS


class TestEnumBranch:
    def test_enum_branch_violation(self, engine):
        """
        Clause 3.3.3: influent_compliance must be '符合国家标准'.
        """
        results = engine.check(
            "wastewater_collection",
            {"system_type": "sewage", "influent_compliance": "不符合"},
            {},
        )
        target = [r for r in results if r.clause == "3.3.3"][0]
        assert target.status == RuleResultStatus.VIOLATION
        assert "influent_compliance" in target.message

    def test_enum_branch_pass(self, engine):
        results = engine.check(
            "wastewater_collection",
            {
                "system_type": "sewage",
                "influent_compliance": "符合国家标准",
                "no_operational_impact": True,
                "no_worker_harm": True,
                "no_reuse_impact": True,
                "no_sludge_impact": True,
            },
            {},
        )
        target = [r for r in results if r.clause == "3.3.3"][0]
        assert target.status == RuleResultStatus.PASS


class TestNestedNumericConditions:
    def test_nested_pressure_test_multiplier_violation(self, engine):
        """
        Clause 8.3.15: pressure_test_multiplier >= 1.5 * working_pressure.
        """
        results = engine.check(
            "sludge_treatment",
            {"system_type": "sewage"},
            {"pressure_test_multiplier": 1.2, "working_pressure": 10.0},
        )
        target = [r for r in results if r.clause == "8.3.15"][0]
        assert target.status == RuleResultStatus.VIOLATION
        assert "pressure_test_multiplier" in target.message

    def test_nested_pressure_test_multiplier_pass(self, engine):
        results = engine.check(
            "sludge_treatment",
            {"system_type": "sewage"},
            {"pressure_test_multiplier": 15.0, "working_pressure": 10.0},
        )
        target = [r for r in results if r.clause == "8.3.15"][0]
        assert target.status == RuleResultStatus.PASS
