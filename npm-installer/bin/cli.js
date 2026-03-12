#!/usr/bin/env node
/**
 * LearnItHard Skills Installer CLI
 * Usage: npx @learnithard/skills-installer
 */

import inquirer from 'inquirer';
import chalk from 'chalk';
import ora from 'ora';
import fs from 'fs-extra';
import { execSync } from 'child_process';
import os from 'os';
import path from 'path';

const SKILLS_REPO = 'https://github.com/LearnItHard/Skills-building';

// Detect installed AI agents
const detectAgents = () => {
  const agents = [];
  const home = os.homedir();
  
  const checks = [
    { name: 'Claude Code', dir: '.claude/skills', id: 'claude-code' },
    { name: 'OpenCode', dir: '.config/opencode/skill', id: 'opencode' },
    { name: 'Codex', dir: '.codex/skills', id: 'codex' },
    { name: 'Cursor', dir: '.cursor/skills', id: 'cursor' },
  ];
  
  for (const check of checks) {
    const fullPath = path.join(home, check.dir);
    if (fs.existsSync(fullPath)) {
      agents.push({ ...check, path: fullPath, installed: true });
    }
  }
  
  return agents;
};

// Fetch available skills from repo
const fetchSkills = async () => {
  const spinner = ora('Fetching skills list...').start();
  
  try {
    // In real implementation, fetch from GitHub API or raw JSON
    // For demo, return static list
    const skills = [
      {
        name: 'mineru-converter',
        description: 'Document conversion using MinerU API',
        category: 'document',
        path: 'skills/mineru-converter'
      },
      {
        name: 'skills-manager',
        description: 'CLI tool to manage AI agent skills',
        category: 'utility',
        path: 'skills/skills-manager'
      }
    ];
    
    spinner.succeed('Skills list loaded');
    return skills;
  } catch (error) {
    spinner.fail('Failed to fetch skills');
    throw error;
  }
};

// Install skill to agents
const installSkill = async (skill, agents) => {
  const spinner = ora(`Installing ${skill.name}...`).start();
  
  try {
    // 1. Clone to temp
    const tempDir = path.join(os.tmpdir(), `skills-install-${Date.now()}`);
    execSync(`git clone --depth 1 ${SKILLS_REPO} ${tempDir}`, { stdio: 'ignore' });
    
    // 2. Install to each agent
    for (const agent of agents) {
      const targetDir = path.join(agent.path, skill.name);
      const sourceDir = path.join(tempDir, skill.path);
      
      // Remove old version
      if (fs.existsSync(targetDir)) {
        fs.removeSync(targetDir);
      }
      
      // Copy new version
      fs.copySync(sourceDir, targetDir);
    }
    
    // 3. Cleanup
    fs.removeSync(tempDir);
    
    spinner.succeed(`${skill.name} installed successfully`);
  } catch (error) {
    spinner.fail(`Failed to install ${skill.name}`);
    throw error;
  }
};

// Main interactive menu
const main = async () => {
  console.log(chalk.cyan.bold('\n📦 LearnItHard Skills Installer\n'));
  
  // Detect agents
  const agents = detectAgents();
  if (agents.length === 0) {
    console.log(chalk.yellow('⚠ No AI agents detected.'));
    console.log('Supported: Claude Code, OpenCode, Codex, Cursor');
    process.exit(1);
  }
  
  console.log(chalk.green(`✓ Detected ${agents.length} agent(s):`));
  agents.forEach(a => console.log(`  • ${a.name}`));
  console.log();
  
  // Fetch skills
  const skills = await fetchSkills();
  
  // Interactive menu
  const { action } = await inquirer.prompt([
    {
      type: 'list',
      name: 'action',
      message: 'What would you like to do?',
      choices: [
        { name: '🔧 Install specific skill', value: 'install' },
        { name: '📋 List all skills', value: 'list' },
        { name: '🗑️ Uninstall skill', value: 'uninstall' },
        { name: '🔄 Update all skills', value: 'update' },
        { name: '❌ Exit', value: 'exit' }
      ]
    }
  ]);
  
  switch (action) {
    case 'install':
      const { skillToInstall } = await inquirer.prompt([
        {
          type: 'list',
          name: 'skillToInstall',
          message: 'Select skill to install:',
          choices: skills.map(s => ({
            name: `${s.name} - ${s.description}`,
            value: s
          }))
        }
      ]);
      
      await installSkill(skillToInstall, agents);
      break;
      
    case 'list':
      console.log(chalk.cyan('\n📚 Available Skills:\n'));
      skills.forEach(s => {
        console.log(`  ${chalk.bold(s.name)}`);
        console.log(`    ${s.description}`);
        console.log(`    Category: ${s.category}\n`);
      });
      break;
      
    case 'uninstall':
      // Implementation for uninstall
      console.log(chalk.yellow('Uninstall feature coming soon...'));
      break;
      
    case 'update':
      // Implementation for update
      console.log(chalk.yellow('Update feature coming soon...'));
      break;
      
    case 'exit':
      console.log(chalk.green('\n👋 Goodbye!\n'));
      process.exit(0);
  }
};

// Run
main().catch(error => {
  console.error(chalk.red('Error:'), error.message);
  process.exit(1);
});
