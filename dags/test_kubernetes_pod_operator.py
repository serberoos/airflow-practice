from datetime import datetime, timedelta
# datetime  : 스케줄링 된 시작날짜를 알기 위함.
# timedelta : 기준 시각에 전 시간 / 후 시간을 알기 위함.

from kubernetes.client import models as k8s
from airflow.models import DAG, Variable
from airflow.operators.dummy_operator import DummyOperator
from airflow.kubernetes.secret import Secret
from airflow.kubernetes.pod import Resources
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator # airflow.contrib.operatos.Kubernetes_pod_operator 는 구버전 | airflow 2.0 버전부터는 지원하지 않는다.

dag_id ='kubernetes-pod-operator-test-dag'

task_default_args= {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2020, 11, 10),
    'depends_on_past': False,
    'email' : ['jae99c@gmail.com'],
    'email_on_retry': False,
    'email_on_failure': True,
    'execution_timeout': timedelta(hours=1)    
}

dag = DAG(
    dag_id=dag_id, # 고유 식별자
    description='test kubernetes pod operator',
    default_args=task_default_args,
    schedule_interval='5 16 * * *', # DAG가 trigger될 빈도를 정의한다.
    max_active_runs=1
)

# env = Secret(
#     'env',
#     'TEST',
#     'test-env',
#     'TEST',
# )

# pod_resources = Resources()
# pod_resources.request_cpu = '1000m'
# pod_resources.request_memory = '2048Mi'
# pod_resources.limit_cpu = '2000m'
# pod_resources.limit_memory = '4096Mi'

"""
    pod의 가용가능 리소스가 한정되어 있다면 resource의 request limit을 정의할 수 있다.
    위처럼 resource로 설정할 수도 있고 kubernetes executor를 사용하고 있는 환경이라면 pod argument에 executor의 리소스를 정의할 수 있다.

    executor_config={
        "KubernetesExecutor": {
            "limit_cpu": "8",
            "limit_memory": "64Gi",
            "request_cpu": "4",
            "request_memory": "32Gi",
        }
    }

"""



configmaps = [
    k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name='airflow-airflow-config')), #configmaps 가져오기
]

"""
    configmaps = [
        k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name='secret')),
    ]

    Secret = Secret(
        'env',
        'Secret',
        'env2',
        'Secret',
    )

    secrets=[env],
    env_from=configmaps
    ---------------------------------------------------------------------------------
    Dockerfile에서 환경 변수로 설정된 값을 Kubernetes configmap 혹은 secret을 통해 설정된 값을 가져오려면 위와 같이 설정이 필요하다.
    만약 위처럼 설정하지 않는다면 환경 변수로 설정된 값을 호출할 수 없다.
"""
start = DummyOperator(task_id="start", dag=dag)

"""
    KubernetesPodOperator를 만들기 위해서는 최소 name, namespace, image, task_id가 필요하다.
"""
run = KubernetesPodOperator(
    task_id="kubernetespodoperator", # task ID
    name="kubernetespodoperator", # task 이름
    namespace='airflow', # kubernetes내에서 실행할 namespace
    image='ubuntu:16.04', # 사용할 도커 이미지
    cmds=["bash", "-cx"],
    arguments=["echo", "helloworld"],
    labels={"foo": "bar"},
    in_cluster=True,
    # secrets=[
    #     env
    # ],
    # image_pull_secrets=[k8s.V1LocalObjectReference('image_credential')], # Public Docker image가 아닌 private Docker image를 가져오려면 image_pull을 할 수 있는 환경 변수 호출을 통해 pull 받아 동작시킬 수 있다.
   
    is_delete_operator_pod=True, # 포트 삭제 여부 false로 설정하면 PodOperator가 동작하고 pod가 삭제되지 않아 메모리를 점유하고 있을 수 있다.
    get_logs=True, # Airflow 환경에서 Pod 동작 log 출력여부
    # resources=pod_resources,
    env_from=configmaps,
    startup_timeout_seconds=500, # default timeout은 120초인데, 이미지를 pull받는 시간 동안 초과될 수가 있음.
    dag=dag,
)

start >> run
