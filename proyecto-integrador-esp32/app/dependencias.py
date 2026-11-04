"""dependencies.py
Codigo para definir las dependencias de la aplicacion
Este arma la cadena get_db → repositorio → servicio en cada peticion
"""

# Importaciones
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.alert_repository import AlertRepository, SqlAlchemyAlertRepository
from app.repositories.reading_repository import (
    ReadingRepository,
    SqlAlchemyReadingRepository,
)
from app.repositories.sensor_repository import (
    SensorRepository,
    SqlAlchemySensorRepository,
)
from app.services.alert_query_service import AlertQueryService
from app.services.anomaly_detection_service import AnomalyDetectionService
from app.services.notifiers import AlertNotifier, LogAlertNotifier
from app.services.reading_service import ReadingService
from app.services.sensor_service import SensorService


def get_alert_repository(db: Session = Depends(get_db)) -> AlertRepository:  # noqa: B008
    return SqlAlchemyAlertRepository(db)


def get_alert_query_service(
    repo: AlertRepository = Depends(get_alert_repository),  # noqa: B008
) -> AlertQueryService:
    return AlertQueryService(repo)


def get_reading_repository(db: Session = Depends(get_db)) -> ReadingRepository:  # noqa: B008
    return SqlAlchemyReadingRepository(db)


def get_sensor_repository(db: Session = Depends(get_db)) -> SensorRepository:  # noqa: B008
    return SqlAlchemySensorRepository(db)


def get_reading_service(
    repo: ReadingRepository = Depends(get_reading_repository),  # noqa: B008
) -> ReadingService:
    return ReadingService(repo)


def get_sensor_service(
    repo: SensorRepository = Depends(get_sensor_repository),  # noqa: B008
) -> SensorService:
    return SensorService(repo)


def get_alert_notifier() -> AlertNotifier:
    return LogAlertNotifier()  # estrategia por defecto; cambia aqui sin tocar
    # el service


def get_anomaly_detection_service(
    alert_repo: AlertRepository = Depends(get_alert_repository),  # noqa: B008
    notifier: AlertNotifier = Depends(get_alert_notifier),  # noqa: B008
    sensor_repo: SensorRepository = Depends(get_sensor_repository),  # noqa: B008
) -> AnomalyDetectionService:
    return AnomalyDetectionService(
        alert_repo=alert_repo, notifier=notifier, sensor_lookup=sensor_repo
    )


# Tipos de dependencias para inyectar en los endpoints
AlertQueryServiceDep = Annotated[AlertQueryService, Depends(get_alert_query_service)]
ReadingServiceDep = Annotated[ReadingService, Depends(get_reading_service)]
SensorServiceDep = Annotated[SensorService, Depends(get_sensor_service)]
AlertRepositoryDep = Annotated[AlertRepository, Depends(get_alert_repository)]
AnomalyDetectionServiceDep = Annotated[
    AnomalyDetectionService, Depends(get_anomaly_detection_service)
]
SensorRepositoryDep = Annotated[SensorRepository, Depends(get_sensor_repository)]
ReadingRepositoryDep = Annotated[ReadingRepository, Depends(get_reading_repository)]