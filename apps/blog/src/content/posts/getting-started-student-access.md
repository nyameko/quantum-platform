---
title: 'Student guide: your first day on Quantum Platform'
description: 'From account verification and research programme membership to a first Jupyter notebook and Slurm run.'
pubDate: 2026-11-07
tags: ['getting started', 'students', 'HPC']
draft: true
---

A research account gives you a place to begin. It does **not** immediately grant a compute allocation.

## 1. Create and secure your account

Visit [Quantum Platform](https://quantum.nyameko.com/), create an account, verify your email, complete your [research profile](https://quantum.nyameko.com/profile/), and configure [multi-factor authentication](https://quantum.nyameko.com/account/mfa/settings/).

Register **public** SSH and WireGuard keys in [Access keys](https://quantum.nyameko.com/account/access-keys/). Never upload private keys. Your key is not active until access is provisioned.

## 2. Request programme membership

Visit [Research programmes](https://quantum.nyameko.com/programmes/). Request membership in the programme associated with your supervisor or project. Approval is separate from signup.

## 3. Confirm your access

Once approved, check [Access & entitlements](https://quantum.nyameko.com/access/) for what has been allocated. Some resources may remain unavailable or require a separate provider approval.

## 4. Open Workbench and run a small experiment

Start [Jupyter Workbench](https://quantum.nyameko.com/workbench/), select an available CPU reference notebook, and verify you can save it in your research home. Go to [Slurm Runs](https://quantum.nyameko.com/runs/) to submit an authorized small CPU job. Track the scheduler job ID, completion status, and results; a submitted job does not prove successful computation.

Use Quantum Guide for explanations and research navigation, but verify your scientific outputs from the actual workflow artifacts.

**Publication check:** review against a live student test account and current provisioning workflow before changing `draft: false`.
