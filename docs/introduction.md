# Introduction

## Objective

This repository provides a dynamic, AI-maintained documentation library for the Air Quality service estate.

## Scope

- Documentation-only repository
- No service source code
- No secrets or sensitive data
- Standardised service descriptions
- Standardised update/interrogation process

## Core Documentation Requirements

For each service and sub-service, document:

1. Purpose and responsibilities
2. Technology stack
3. Architecture style/components
4. Hosting and runtime environment
5. Repository metadata (URL, branch scope, last analysed details)
6. Key integrations and data flows

## Standard Repository Metadata

Each tracked repository should include:

- Repository URL
- Date created (`created_at_utc`)
- Date last modified (`last_modified_at_utc`, derived from main-branch activity)
- Active status (`Active` / `Monitoring` / `Inactive`)
- Type classification
- Connected services

## Primary Service Domains

- Citizen Services
- Data Services

Each domain contains:

- A high-level overview document
- A sub-folder per sub-service
- A consistent service profile document per sub-service
