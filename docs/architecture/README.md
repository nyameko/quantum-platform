# Architecture

## Public layer

The `quantum-platform` repository contains three separately deployable Astro applications:

- `blog` — `blog.nyameko.com`
- `wiki` — `wiki.quantum.nyameko.com`
- `users` — `users.quantum.nyameko.com`

They share UI components and platform metadata, but remain independent deployments.

## Private infrastructure

Production infrastructure remains in `infra-hpc-qc-k8s`.

The users application will eventually use PostgreSQL with persistent storage provided by Cinder through the
Kubernetes storage layer. No database credentials or production data are stored in this repository.

## Security boundary

Public source does not imply public infrastructure access. The repository is designed to be public while
operational services such as Grafana, Wazuh, JupyterHub, Pi-hole, and Slurm remain VPN-only.
