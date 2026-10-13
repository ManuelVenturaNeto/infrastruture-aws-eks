# airflow

Airflow 3 com `KubernetesExecutor`: cada task roda num pod próprio. As DAGs
chegam por git-sync, os metadados ficam num RDS (*Relational Database Service*)
Postgres e os logs das tasks no S3 (*Simple Storage Service*). Comandos no
[README da infraestrutura](../../README.md).

```mermaid
flowchart TB
  G[GitHub main<br/>process/src/airflow] e1@-->|git-sync| P[Scheduler e<br/>DAG processor]
  P e2@-->|KubernetesExecutor| W[Pod por task]
  W e3@-->|SparkKubernetesOperator| S[SparkApplication<br/>em spark-jobs]
  P e4@--> R[(RDS Postgres<br/>metadados)]
  W e5@-->|logs| B[(S3<br/>kube-system-airflow)]
  U[UI: port-forward 8080] e6@--> A[API server]
  A e7@--> R
  P e8@-->|roda em| N[NodePool airflow<br/>on-demand]

  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
  e4@{ animate: true }
  e5@{ animate: true }
  e6@{ animate: true }
  e7@{ animate: true }
  e8@{ animate: true }

  classDef data fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  classDef compute fill:#ffedd5,stroke:#ea580c,color:#7c2d12
  classDef orchestration fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
  classDef infra fill:#dcfce7,stroke:#16a34a,color:#14532d

  class G,R,B data
  class W,S compute
  class P,A,U orchestration
  class N infra
```

A UI (*User Interface*) é acessada por `port-forward`; o login é `admin` /
`admin`.
