# FlotaTrack-EDSIA — Diagramas UML
## 1. Diagrama de clases (modelos SQLAlchemy)

```mermaid
classDiagram
    direction LR

    class Truck {
        +String id
        +String plates
        +String model
        +Float capacity_kg
        +String security_state
        +DateTime created_at
    }

    class TelemetryReading {
        +String id
        +String truck_id
        +Float latitude
        +Float longitude
        +Float speed_kmh
        +Float fuel_level_pct
        +DateTime recorded_at
    }

    class Command {
        +String id
        +String truck_id
        +String type
        +String status
        +DateTime requested_at
        +DateTime applied_at
    }

    class Driver {
        +String id
        +String name
        +String license_number
        +String phone
    }

    class Trip {
        +String id
        +String truck_id
        +String driver_id
        +String origin
        +String destination
        +String cargo_description
        +DateTime started_at
        +DateTime finished_at
    }

    class CartaPorteRecord {
        +String id
        +String trip_id
        +String folio
        +String emisor_rfc
        +String receptor_rfc
        +String tipo_cfdi
        +origen_* (clave, calle, colonia, municipio, estado, CP, fecha_hora_salida)
        +destino_* (clave, calle, colonia, municipio, estado, CP, fecha_hora_llegada)
        +Float distancia_recorrida_km
        +mercancia_* (clave_prod_serv, peso_bruto_kg, peso_neto_kg, clave_unidad, embalaje)
        +String merchandise_description
        +Boolean material_peligroso
        +String tipo_transporte
        +String config_vehicular
        +String placa_camion
        +String placa_remolque
        +String numero_permiso_sict
        +String aseguradora_nombre
        +String poliza_numero
        +operador_* (nombre, rfc, licencia, domicilio)
    }

    class SecurityState {
        <<enumeration>>
        active
        locked
    }
    class CommandType {
        <<enumeration>>
        lock
        unlock
    }
    class CommandStatus {
        <<enumeration>>
        pending
        applied
        cancelled
    }
    class TipoCfdi {
        <<enumeration>>
        Ingreso
        Traslado
    }
    class TipoTransporte {
        <<enumeration>>
        Terrestre
        Aéreo
        Marítimo
        Ferroviario
    }

    Truck "1" *-- "0..*" TelemetryReading : telemetry_readings
    Truck "1" *-- "0..*" Command : commands
    Truck "1" o-- "0..*" Trip : trips
    Driver "1" o-- "0..*" Trip : trips
    Trip "1" *-- "0..1" CartaPorteRecord : carta_porte

    Truck ..> SecurityState
    Command ..> CommandType
    Command ..> CommandStatus
    CartaPorteRecord ..> TipoCfdi
    CartaPorteRecord ..> TipoTransporte
```

> Los rombos rellenos (`*--`) indican composición: al borrar un `Truck` se borran sus lecturas y comandos, y al borrar un `Trip` se borra su carta porte (`cascade="all, delete-orphan"`). `CartaPorteRecord` tiene un solo registro por viaje (`trip_id` único). Los campos agrupados con `*` representan varias columnas del mismo bloque.


 Diagramas UML FORMATO .PNG
<img width="1092" height="875" alt="image" src="https://github.com/user-attachments/assets/343504a5-c162-451b-9b21-270f4e1608c6" />

