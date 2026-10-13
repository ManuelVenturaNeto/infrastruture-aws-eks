# mlflow

Servidor do MLflow com o backend de experimentos num RDS (*Relational Database
Service*) Postgres e os artefatos no S3 (*Simple Storage Service*), servidos
pelo próprio servidor. Comandos no [README da infraestrutura](../../README.md).

```mermaid
flowchart TB
  U[UI e clientes:<br/>port-forward 5000] e1@--> M[MLflow server]
  M e2@-->|experimentos| R[(RDS Postgres)]
  M e3@-->|artefatos| B[(S3<br/>kube-system-mlflow)]
  M e4@-->|roda em| N[NodePool mlflow<br/>on-demand]

  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
  e4@{ animate: true }

  classDef data fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  classDef compute fill:#ffedd5,stroke:#ea580c,color:#7c2d12
  classDef orchestration fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
  classDef infra fill:#dcfce7,stroke:#16a34a,color:#14532d

  class R,B data
  class M compute
  class U orchestration
  class N infra
```

A UI (*User Interface*) é acessada por `port-forward`.
