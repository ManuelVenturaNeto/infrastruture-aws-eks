# spark

Spark Operator, NodePools `spark` e `spark-gpu` e Spark History Server. Os jobs
rodam no namespace `spark-jobs`, leem e escrevem no lake do S3 (*Simple Storage
Service*) e gravam os event logs que o History Server mostra. Comandos no
[README da infraestrutura](../../README.md).

```mermaid
flowchart TB
  A[Airflow worker] e1@-->|airflow-rbac.yaml| S[SparkApplication<br/>em spark-jobs]
  O[Spark Operator] e2@--> S
  S e3@--> D[Driver]
  D e4@--> E[Executors]
  E e5@-->|roda em| N[NodePools spark e spark-gpu<br/>spot; on-demand só se CRITICAL]
  E e6@-->|Pod Identity| L[(Lake<br/>kube-system-lake)]
  D e7@-->|event logs| B[(S3<br/>kube-system-spark)]
  H[History Server<br/>on-demand] e8@--> B
  U[UI: port-forward 18080] e9@--> H

  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
  e4@{ animate: true }
  e5@{ animate: true }
  e6@{ animate: true }
  e7@{ animate: true }
  e8@{ animate: true }
  e9@{ animate: true }

  classDef data fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  classDef compute fill:#ffedd5,stroke:#ea580c,color:#7c2d12
  classDef orchestration fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
  classDef infra fill:#dcfce7,stroke:#16a34a,color:#14532d

  class L,B data
  class D,E,H compute
  class A,O,S,U orchestration
  class N infra
```

A UI (*User Interface*) do History Server é acessada por `port-forward`.
