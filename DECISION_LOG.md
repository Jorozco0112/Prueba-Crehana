# Decision Log

Registro de las decisiones técnicas del proyecto. Cada entrada sigue el formato:
**Contexto** → **Decisión** → **Alternativas descartadas** → **Consecuencias**.

---

## Índice

- [DEC-001 · DDD táctico y pragmático](#dec-001--ddd-táctico-y-pragmático)
- [DEC-002 · Entidades y propiedad de las listas](#dec-002--entidades-y-propiedad-de-las-listas)
- [DEC-003 · Task es un aggregate independiente de TaskList](#dec-003--task-es-un-aggregate-independiente-de-tasklist)
- [DEC-004 · Estados de una tarea y transiciones](#dec-004--estados-de-una-tarea-y-transiciones)
- [DEC-005 · Prioridad con orden explícito](#dec-005--prioridad-con-orden-explícito)
- [DEC-006 · Orden de implementación](#dec-006--orden-de-implementación)
- [DEC-007 · La "invitación" es un aviso de asignación](#dec-007--la-invitación-es-un-aviso-de-asignación)
- [DEC-008 · Porcentaje de completitud calculado en cada consulta](#dec-008--porcentaje-de-completitud-calculado-en-cada-consulta)
- [DEC-009 · Cuatro capas con dependencias hacia adentro](#dec-009--cuatro-capas-con-dependencias-hacia-adentro)
- [DEC-010 · Dominio en Python puro; Pydantic en los bordes; mypy para el tipado](#dec-010--dominio-en-python-puro-pydantic-en-los-bordes-mypy-para-el-tipado)
- [DEC-011 · Puertos definidos en application con ABC](#dec-011--puertos-definidos-en-application-con-abc)
- [DEC-012 · Una clase por caso de uso, que devuelve entidades](#dec-012--una-clase-por-caso-de-uso-que-devuelve-entidades)
- [DEC-013 · Conexión de dependencias con Depends, sin librería de inyección](#dec-013--conexión-de-dependencias-con-depends-sin-librería-de-inyección)
- [DEC-014 · PostgreSQL como base de datos](#dec-014--postgresql-como-base-de-datos)
- [DEC-015 · Acceso síncrono a la base de datos](#dec-015--acceso-síncrono-a-la-base-de-datos)
- [DEC-016 · SQLAlchemy 2.0 con modelos ORM separados del dominio](#dec-016--sqlalchemy-20-con-modelos-orm-separados-del-dominio)
- [DEC-017 · El caso de uso decide cuándo se confirma la transacción](#dec-017--el-caso-de-uso-decide-cuándo-se-confirma-la-transacción)
- [DEC-018 · Migraciones con Alembic en un servicio aparte de docker-compose](#dec-018--migraciones-con-alembic-en-un-servicio-aparte-de-docker-compose)
- [DEC-019 · Representación de estado y prioridad en la base de datos](#dec-019--representación-de-estado-y-prioridad-en-la-base-de-datos)
- [DEC-020 · Rutas: anidar solo cuando la operación necesita a la lista](#dec-020--rutas-anidar-solo-cuando-la-operación-necesita-a-la-lista)
- [DEC-021 · Identificadores UUID v7 generados por el dominio](#dec-021--identificadores-uuid-v7-generados-por-el-dominio)
- [DEC-022 · Edición parcial con PATCH](#dec-022--edición-parcial-con-patch)
- [DEC-023 · Estado y responsable como sub-recursos con PUT](#dec-023--estado-y-responsable-como-sub-recursos-con-put)
- [DEC-024 · Filtros, paginación, orden y forma del listado](#dec-024--filtros-paginación-orden-y-forma-del-listado)
- [DEC-025 · Códigos de respuesta](#dec-025--códigos-de-respuesta)
- [DEC-026 · 404 para lo que no se puede ver, 403 para lo que no se puede hacer](#dec-026--404-para-lo-que-no-se-puede-ver-403-para-lo-que-no-se-puede-hacer)
- [DEC-027 · Excepciones por categoría y un único handler](#dec-027--excepciones-por-categoría-y-un-único-handler)
- [DEC-028 · Formato de error único basado en Problem Details (RFC 9457)](#dec-028--formato-de-error-único-basado-en-problem-details-rfc-9457)
- [DEC-029 · Cada capa valida lo que puede saber](#dec-029--cada-capa-valida-lo-que-puede-saber)
- [DEC-030 · Autenticación con JWT](#dec-030--autenticación-con-jwt)
- [DEC-031 · Contraseñas](#dec-031--contraseñas)
- [DEC-032 · Destinatarios del aviso de asignación](#dec-032--destinatarios-del-aviso-de-asignación)
- [DEC-033 · Notificación de mejor esfuerzo, con un puerto que expresa la intención](#dec-033--notificación-de-mejor-esfuerzo-con-un-puerto-que-expresa-la-intención)
- [DEC-034 · Estrategia de testing](#dec-034--estrategia-de-testing)
- [DEC-035 · Base de datos de tests en docker-compose](#dec-035--base-de-datos-de-tests-en-docker-compose)
- [DEC-036 · Aislamiento de tests con TRUNCATE](#dec-036--aislamiento-de-tests-con-truncate)
- [DEC-037 · Implementaciones falsas en lugar de mocks](#dec-037--implementaciones-falsas-en-lugar-de-mocks)
- [DEC-038 · El tiempo es una dependencia explícita](#dec-038--el-tiempo-es-una-dependencia-explícita)
- [DEC-039 · Python 3.14 y uv](#dec-039--python-314-y-uv)
- [DEC-040 · Calidad de código: flake8, black, isort, mypy y pre-commit](#dec-040--calidad-de-código-flake8-black-isort-mypy-y-pre-commit)
- [DEC-041 · Integración continua con GitHub Actions](#dec-041--integración-continua-con-github-actions)
- [DEC-042 · Configuración por variables de entorno](#dec-042--configuración-por-variables-de-entorno)
- [DEC-043 · Docker: tres etapas y perfiles de docker-compose](#dec-043--docker-tres-etapas-y-perfiles-de-docker-compose)
- [DEC-044 · Documentación, idioma y commits](#dec-044--documentación-idioma-y-commits)
- [DEC-045 · Ajustes durante la implementación](#dec-045--ajustes-durante-la-implementación)
- [Pendientes y extensiones futuras](#pendientes-y-extensiones-futuras)

---

## DEC-001 · DDD táctico y pragmático

**Contexto.** El enunciado pide una estructura por capas (Domain, Application/Use Cases,
Infrastructure). El dominio es pequeño: un gestor de listas de tareas.

**Decisión.** Aplicar solo los patrones tácticos de DDD que aportan valor en este tamaño:
entidades con comportamiento, value objects, repositorios definidos como interfaces (puertos)
y excepciones propias del dominio.

**Alternativas descartadas.**
- *Bounded contexts*: hay un único contexto; dividirlo sería ceremonia sin beneficio.
- *Domain events*: solo existe un efecto secundario (la notificación de asignación). Un
  mecanismo de eventos no se justifica para un único consumidor.
- *CQRS*: lecturas y escrituras comparten modelo sin problemas de rendimiento.

**Consecuencias.** Menos indirección y código más fácil de seguir. Si aparecieran más efectos
secundarios encadenados, introducir domain events sería el siguiente paso natural.

---

## DEC-002 · Entidades y propiedad de las listas

**Contexto.** El enunciado no dice si una lista tiene dueño. Sin embargo, se implementará JWT,
y autenticar sin autorizar dejaría que cualquier usuario autenticado borre listas ajenas.

**Decisión.** Tres entidades: `TaskList`, `Task` y `User`.

| Acción | Dueño de la lista | Asignado a la tarea | Otro usuario |
|---|---|---|---|
| Ver, editar y eliminar la lista | Sí | No | No |
| Crear, editar y eliminar tareas | Sí | No | No |
| Ver la tarea asignada | Sí | Sí | No |
| Cambiar el estado de la tarea | Sí | Sí | No |

El asignado consulta sus tareas desde un endpoint propio (p. ej. `GET /users/me/tasks`), sin
acceso al resto de la lista.

**Alternativas descartadas.**
- *Listas visibles para cualquier usuario autenticado*: la autenticación quedaría sin
  autorización.
- *El asignado sin ningún acceso*: la asignación sería un dato sin uso.
- *Listas compartidas con miembros/colaboradores*: requiere un modelo de membresía que no está
  en el alcance.

**Consecuencias.** Es el mínimo que le da sentido a la asignación sin introducir membresías.
Todo caso de uso recibe al usuario actual y valida sus permisos antes de operar. El usuario
actual se obtiene de una única dependencia (`get_current_user`), de modo que el mecanismo de
autenticación puede cambiar sin tocar los casos de uso.

---

## DEC-003 · `Task` es un aggregate independiente de `TaskList`

**Contexto.** Un aggregate existe para proteger una regla de negocio que involucra a varios
objetos a la vez. Se revisó si alguna regla obliga a validar todas las tareas de una lista al
modificar una sola:

| Regla | ¿Necesita todas las tareas al escribir? |
|---|---|
| Porcentaje de completitud | No: es una lectura; ninguna escritura depende de él |
| Solo el dueño agrega tareas | No: necesita la lista (su dueño), no sus tareas |
| Eliminar una lista elimina sus tareas | No: es ciclo de vida, se resuelve con borrado en cascada |

**Decisión.** `Task` es su propio aggregate y referencia a `TaskList` por identidad
(`list_id`), siguiendo la heurística de aggregates pequeños referenciados por ID.

**Alternativas descartadas.**
- *`TaskList` como aggregate que contiene sus tareas*: cambiar el estado de una tarea obligaría
  a cargar la lista completa, y dos usuarios modificando tareas distintas de la misma lista
  entrarían en conflicto sin necesidad.

**Consecuencias.** Dos repositorios (`TaskListRepository`, `TaskRepository`). Los filtros y la
paginación viven en `TaskRepository`, y modificar una tarea carga una sola fila. Si apareciera
una regla que cruce tareas (p. ej. "máximo N tareas por lista"), esta decisión se revisaría.

---

## DEC-004 · Estados de una tarea y transiciones

**Contexto.** El enunciado pide poder cambiar el estado de una tarea como caso de uso separado
de actualizarla.

**Decisión.**
- Estados: `PENDING`, `IN_PROGRESS`, `COMPLETED`.
- Se permite cualquier transición: en la práctica una tarea puede completarse directamente o
  reabrirse si al revisarla faltaba algo.
- El cambio pasa siempre por `Task.change_status(new_status, at=now)`. Al pasar a `COMPLETED`
  se registra `completed_at` con el momento recibido (DEC-038); al salir de `COMPLETED` se borra.
- Cambiar al mismo estado no hace nada (en particular, no sobrescribe `completed_at`).

**Alternativas descartadas.**
- *Estado `BACKLOG`*: solo se distingue de `PENDING` si existen sprints (una tarea creada pero
  sin sprint asignado). No hay sprints en el alcance.
- *Máquina de estados restrictiva*: no hay requisito que la pida y bloquearía casos reales como
  reabrir una tarea.
- *Estado como entidad configurable (nombre, color)*: el color es presentación, no dominio, y un
  catálogo de estados agregaría un CRUD que nadie pidió.

**Consecuencias.** `change_status()` tiene comportamiento real (no es un setter), lo que evita
un modelo anémico. Si el negocio exigiera restringir transiciones, la regla se agrega en ese
único método sin tocar las demás capas. Cambiar el estado es una operación separada de editar
la tarea porque tiene permisos distintos: el asignado puede hacer lo primero pero no lo segundo
(DEC-002).

---

## DEC-005 · Prioridad con orden explícito

**Decisión.** `LOW` (0), `MEDIUM` (1), `HIGH` (2), `URGENT` (3). Cada valor lleva un orden
numérico de importancia.

**Alternativas descartadas.**
- *Solo strings*: ordenar alfabéticamente da un orden incorrecto ("HIGH" < "LOW" < "MEDIUM").

**Consecuencias.** Las tareas pueden ordenarse por importancia real. En la base de datos se guarda
el entero y la API expone el nombre (DEC-019).

---

## DEC-006 · Orden de implementación

**Contexto.** Tiempo estimado de 4 a 6 horas. El enunciado indica priorizar lo principal y
documentar lo pendiente.

**Decisión.**
1. Core (listas, tareas, estados, filtros, completitud), tests y Docker.
2. `User`, base común de la autenticación y la asignación.
3. Autenticación con JWT.
4. Asignación de tareas.
5. Notificación ficticia.

**Consecuencias.** Si el tiempo no alcanza, lo que queda fuera son bonus y el entregable
principal está completo. La notificación es la más barata de los bonus y la que mejor muestra
la separación entre puertos y adaptadores.

---

## DEC-007 · La "invitación" es un aviso de asignación

**Contexto.** El enunciado pide una "simulación de envío de invitación a usuarios por email"
sin especificar a qué se invita.

**Decisión.** Al asignar una tarea a un usuario, se le envía un aviso por email simulado.

**Alternativas descartadas.**
- *Invitar a colaborar en una lista*: requiere un modelo de miembros que contradice DEC-002.
- *Invitar a registrarse en la aplicación*: no se conecta con el dominio de tareas.

**Consecuencias.** La notificación depende de la asignación y se implementa al final (DEC-006).

---

## DEC-008 · Porcentaje de completitud calculado en cada consulta

**Contexto.** El listado de tareas de una lista admite filtros por estado y prioridad, y debe
incluir un campo con el porcentaje de completitud.

**Decisión.**
- El porcentaje es una propiedad de la lista: `COMPLETED / total de tareas de la lista`.
- Los filtros deciden qué tareas se muestran, pero no afectan al porcentaje.
- Se calcula en cada consulta con una agregación aparte sobre toda la lista
  (`count(*) FILTER (WHERE status = 'COMPLETED')` y `count(*)`), independiente de la paginación.
- La regla (redondeo y caso borde) vive en el dominio, en el value object
  `CompletionPercentage.from_counts(completed, total)`; el conteo lo hace el repositorio.
- Una lista sin tareas devuelve 0%. La respuesta incluye además `total_tasks` y
  `completed_tasks`, de modo que el cliente distingue una lista vacía (`total_tasks: 0`) de una
  lista sin avances.

**Alternativas descartadas.**
- *Lista vacía al 100%* ("todas sus tareas, ninguna, están completas"): una lista recién creada
  aparecería como terminada.
- *Lista vacía como `null`*: semánticamente honesto, pero obliga a cada cliente a manejar el
  caso nulo; los conteos resuelven la ambigüedad sin ese costo.
- *Calcularlo sobre las tareas filtradas*: con `status=COMPLETED` siempre daría 100% y con
  `status=PENDING` siempre 0%, un dato sin información.
- *Porcentaje por tarea*: crearía dos fuentes de verdad para el mismo hecho (¿una tarea
  `COMPLETED` al 40%?).
- *Guardarlo en la tabla de listas*: es un dato derivado. Obliga a actualizarlo en cada
  creación, eliminación y cambio de estado, y expone a escrituras concurrentes que se pisan. No
  hay un problema de rendimiento medido que justifique desnormalizar.

**Consecuencias.** Una consulta adicional y barata (con índice en `list_id`) por cada listado.
Si en el futuro hiciera falta optimizar, se guardarían contadores (`total`, `completed`), no el
porcentaje.

---

## DEC-009 · Cuatro capas con dependencias hacia adentro

**Contexto.** El enunciado exige una estructura limpia por capas (Domain, Application/Use
Cases, Infrastructure).

**Decisión.** Cuatro capas. Las dependencias solo apuntan hacia el centro:

```
entrypoints (FastAPI) ──┐
                        ├──►  application  ──►  domain
infrastructure (SQLA) ──┘
```

| Capa | Contiene | Puede importar |
|---|---|---|
| `domain` | Entidades, value objects y excepciones del dominio | Solo la biblioteca estándar |
| `application` | Casos de uso e interfaces (puertos) de repositorios y servicios externos | `domain` |
| `infrastructure` | Implementaciones de los puertos: SQLAlchemy, email simulado, JWT, hashing | `application`, `domain` |
| `entrypoints` | Rutas FastAPI, schemas Pydantic, traducción de excepciones a HTTP | `application`, `domain` (e `infrastructure` solo para conectar dependencias, DEC-013) |

**Alternativas descartadas.**
- *Estructura plana por tipo de archivo (`routers/`, `models/`, `services/`)*: más simple, pero
  mezcla reglas de negocio con detalles del framework y no permite probar casos de uso sin base
  de datos.

**Consecuencias.** Los casos de uso se prueban con implementaciones en memoria de los puertos.
El cumplimiento de la regla se puede verificar revisando los imports de cada capa.

---

## DEC-010 · Dominio en Python puro; Pydantic en los bordes; mypy para el tipado

**Contexto.** El enunciado pide "tipado fuerte con Pydantic" y, a la vez, una capa de dominio
independiente.

**Decisión.**
- Entidades y value objects son clases normales de Python, sin dependencias externas.
  `TaskStatus` y `Priority` son `Enum`.
- Las entidades protegen su estado: los atributos con reglas (como `status`) son propiedades de
  solo lectura y cambian únicamente a través de métodos (`change_status()`). Dos entidades son
  iguales si tienen el mismo ID.
- Pydantic se usa donde los datos entran o salen del sistema: schemas de request y response en
  `entrypoints`.
- El tipado estático de todas las capas se verifica con mypy en modo estricto.

**Alternativas descartadas.**
- *Entidades como modelos Pydantic*: acopla el dominio a una librería externa y mezcla la
  validación de formato con las reglas de negocio.
- *`dataclasses`*: también son biblioteca estándar, pero generan atributos públicos y
  modificables, e igualdad por todos los campos. En las entidades habría que contrarrestar ambas
  cosas; se prefieren clases explícitas.

**Consecuencias.** `Task` tiene varias representaciones (entidad, modelo de base de datos,
schemas de entrada y salida) y hace falta código que convierta entre ellas. Es el costo asumido
de mantener el dominio aislado.

---

## DEC-011 · Puertos definidos en `application` con `ABC`

**Contexto.** Los casos de uso necesitan persistencia y servicios externos sin depender de cómo
están implementados.

**Decisión.** Las interfaces de repositorios (`TaskRepository`, `TaskListRepository`,
`UserRepository`), la `UnitOfWork` (DEC-017) y los servicios externos
(`TaskAssignmentNotifier`, `PasswordHasher`, `TokenService`, `Clock`) se definen en
`application` como clases abstractas (`ABC`). Los puertos se
nombran por la intención del caso de uso, no por la tecnología que los implementa (DEC-033).

**Alternativas descartadas.**
- *Interfaces en `domain`*: tiene sentido cuando las entidades usan los repositorios. Aquí solo
  los usan los casos de uso, y la interfaz pertenece a quien la usa (inversión de dependencias).
- *`typing.Protocol`*: más flexible, pero solo se verifica con mypy. `ABC` falla al instanciar
  una implementación incompleta y declara explícitamente que la clase es un puerto.

**Consecuencias.** Cada caso de uso puede probarse con implementaciones falsas de sus puertos.

---

## DEC-012 · Una clase por caso de uso, que devuelve entidades

**Decisión.**
- Cada caso de uso es una clase con un único método `execute()`, en su propio archivo.
- Recibe en el constructor solo los puertos que necesita.
- Recibe parámetros simples u objetos definidos en `application`, nunca los schemas HTTP.
- Devuelve entidades del dominio. Para resultados compuestos (el listado con conteos y
  porcentaje) devuelve una clase de resultado definida en `application`.
- `entrypoints` convierte las entidades a schemas de respuesta con
  `TaskResponse.model_validate(task, from_attributes=True)`.

**Alternativas descartadas.**
- *Servicios que agrupan métodos (`TaskService`)*: menos archivos, pero cada servicio acumula las
  dependencias de todos sus métodos (cambiar el estado cargaría con el notificador de la
  asignación) y tiende a crecer sin límite.
- *Devolver DTOs de Pydantic desde `application`*: el contrato HTTP quedaría definido en los
  casos de uso, y cambiar la respuesta de la API obligaría a modificarlos.

**Consecuencias.** La carpeta de casos de uso describe lo que hace el sistema: cualquier
ingeniero entiende qué hace cada archivo por su nombre. Se aceptan más archivos a cambio de esa
claridad.

---

## DEC-013 · Conexión de dependencias con `Depends`, sin librería de inyección

**Decisión.** Funciones en `entrypoints/api/dependencies.py` construyen cada caso de uso con
sus implementaciones concretas, y las rutas los reciben mediante `Depends`. Es el único lugar
del código que conoce todas las capas.

**Alternativas descartadas.**
- *Crear los objetos dentro de cada ruta*: la ruta conocería la infraestructura y no se podría
  reemplazar en los tests.
- *`dependency-injector` u otra librería*: dependencia extra y complejidad que no justifica una
  quincena de casos de uso.

**Consecuencias.** La sesión de base de datos vive lo que dura cada request. En los tests,
cualquier dependencia se reemplaza con `app.dependency_overrides`.

---

## DEC-014 · PostgreSQL como base de datos

**Contexto.** El enunciado pide "una base de datos real de tu preferencia".

**Decisión.** PostgreSQL, por razones concretas de este proyecto:
- Los datos son relacionales (usuarios → listas → tareas): claves foráneas, borrado en cascada e
  integridad garantizada por la base de datos.
- El cálculo de completitud (DEC-008) usa `COUNT(*) FILTER (WHERE ...)`.
- Las migraciones son transaccionales: si una migración falla a la mitad, se revierte completa.
- Restricciones `CHECK` para que la base de datos rechace estados y prioridades inválidos.

**Alternativas descartadas.**
- *MySQL*: no soporta `FILTER` y cada `ALTER TABLE` hace commit implícito, por lo que una
  migración fallida puede quedar a medias.
- *SQLite*: un solo escritor a la vez y no corre como servicio aparte. Probar con SQLite y
  desplegar con PostgreSQL haría que los tests no validen el motor real.
- *MongoDB u otra NoSQL*: habría que emular en la aplicación las relaciones y la integridad que
  PostgreSQL ya ofrece.

**Consecuencias.** Los tests de integración corren contra PostgreSQL, el mismo motor que
producción.

---

## DEC-015 · Acceso síncrono a la base de datos

**Contexto.** FastAPI admite endpoints síncronos y asíncronos, y SQLAlchemy ofrece ambas APIs.

**Decisión.** SQLAlchemy síncrono con el driver psycopg 3 (`postgresql+psycopg://`). Todos los
endpoints que acceden a la base de datos se definen con `def`, nunca con `async def`.

**Alternativas descartadas.**
- *SQLAlchemy asíncrono con `asyncpg`*: lo asíncrono rinde cuando un request espera varias
  operaciones de red en paralelo, y este sistema es un CRUD sin ese patrón. Además introduce
  complejidad (errores `MissingGreenlet` con carga diferida, `expire_on_commit`, pytest-asyncio)
  que no aporta valor aquí.

**Consecuencias.** FastAPI ejecuta los endpoints `def` en un pool de hilos (40 por defecto), lo
que limita la concurrencia máxima. Un endpoint `async def` que llamara a la base de datos
síncrona bloquearía el *event loop* de todo el servidor; por eso la regla anterior es estricta.
Migrar a asíncrono más adelante implicaría cambiar las firmas de puertos y casos de uso.

---

## DEC-016 · SQLAlchemy 2.0 con modelos ORM separados del dominio

**Decisión.**
- SQLAlchemy 2.0 con su API tipada (`Mapped[...]`, `mapped_column`), compatible con mypy
  (DEC-010).
- Modelos ORM propios en `infrastructure` (`TaskModel`, `TaskListModel`, `UserModel`) y
  funciones explícitas que convierten entre modelos ORM y entidades del dominio.

**Alternativas descartadas.**
- *SQLModel*: une Pydantic y el ORM en una misma clase, justo lo que DEC-010 evita.
- *Mapeo imperativo de SQLAlchemy sobre las clases del dominio*: evita los modelos intermedios,
  pero SQLAlchemy modifica las clases del dominio en tiempo de ejecución (les inyecta estado
  interno y reemplaza sus atributos). Chocaría con las propiedades de solo lectura de DEC-010 y
  el dominio sería puro solo en apariencia.

**Consecuencias.** Más código de conversión, un costo ya asumido en DEC-010. El dominio no sabe
que existe una base de datos. SQLAlchemy es además la herramienta con la que el equipo tiene más
experiencia, lo que reduce el riesgo en una prueba con tiempo limitado.

---

## DEC-017 · El caso de uso decide cuándo se confirma la transacción

**Contexto.** Hoy ningún caso de uso hace más de una escritura: el único candidato, eliminar una
lista con sus tareas, lo resuelve la base de datos con `ON DELETE CASCADE` en una sola
sentencia.

**Decisión.**
- Un puerto mínimo `UnitOfWork` en `application`, con `commit()` y `rollback()`.
- Su implementación envuelve la `Session` de SQLAlchemy. Los repositorios solo agregan cambios a
  la sesión, sin confirmarlos, y todos comparten la misma sesión por request (DEC-013).
- Cada caso de uso llama a `uow.commit()` cuando termina su operación de negocio. Los efectos
  externos, como la notificación, ocurren después del commit.

**Alternativas descartadas.**
- *Commit en cada operación del repositorio*: funciona mientras no haya casos con varias
  escrituras, pero pone en la capa de persistencia una decisión de negocio (cuándo termina una
  operación). Si apareciera un caso con dos escrituras (p. ej. eliminar un usuario y desasignar
  sus tareas), no podrían combinarse sin reescribir los repositorios.
- *Commit al cerrar la sesión en la dependencia de FastAPI*: el commit quedaría fuera del caso de
  uso, después de efectos externos como el envío del email, y atado a un detalle del framework
  cuyo momento de ejecución respecto a la respuesta ha cambiado entre versiones.
- *Unit of Work completa (con los repositorios como atributos)*: más estructura de la que
  necesita un sistema sin operaciones de varias escrituras.

**Consecuencias.** Nunca se envía un aviso por una asignación que no llegó a guardarse. Los tests
unitarios pueden verificar que el caso de uso confirmó la transacción.

---

## DEC-018 · Migraciones con Alembic en un servicio aparte de docker-compose

**Decisión.**
- El esquema se versiona con Alembic.
- docker-compose define un servicio `migrate` que ejecuta `alembic upgrade head` y termina.
- La API arranca solo si `migrate` terminó bien (`condition: service_completed_successfully`),
  y `migrate` espera a que PostgreSQL esté listo (`healthcheck` con `pg_isready`).

**Alternativas descartadas.**
- *`Base.metadata.create_all()` al arrancar*: no versiona el esquema ni permite evolucionarlo.
- *Ejecutar las migraciones a mano después de levantar los contenedores*: un paso olvidado deja
  la API respondiendo errores 500 por tablas inexistentes.
- *Migrar al arrancar el contenedor de la API*: mezcla dos responsabilidades y, con varias
  réplicas, las migraciones correrían en paralelo.

**Consecuencias.** `docker compose up` deja el sistema funcionando. La migración sigue siendo un
paso explícito y separado de la aplicación, equivalente a un job de migración en producción.

---

## DEC-019 · Representación de estado y prioridad en la base de datos

**Decisión.**
- `priority`: entero (0 a 3) con `CHECK (priority BETWEEN 0 AND 3)`. Permite ordenar por
  importancia directamente en SQL.
- `status`: texto con `CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED'))`.
- La API expone siempre los nombres (`"HIGH"`, `"COMPLETED"`), nunca los valores internos.

**Alternativas descartadas.**
- *Prioridad como texto*: el orden alfabético no coincide con la importancia.
- *Tipo `ENUM` nativo de PostgreSQL para el estado*: agregar un valor requiere `ALTER TYPE`, que
  Alembic no genera automáticamente.

**Consecuencias.** La conversión entre nombres y valores de base de datos ocurre en las funciones
de conversión de `infrastructure` (DEC-016).

---

## DEC-020 · Rutas: anidar solo cuando la operación necesita a la lista

**Contexto.** Las tareas pertenecen a una lista, pero el asignado no tiene acceso a la lista
(DEC-002).

**Decisión.** Las tareas se anidan bajo la lista solo para crearlas y listarlas. Las operaciones
sobre una tarea ya identificada usan rutas planas. Todas las rutas llevan el prefijo `/api/v1`.

| Método | Ruta | Operación | Quién puede |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Registrarse | Público |
| POST | `/api/v1/auth/login` | Obtener un token de acceso | Público |
| POST | `/api/v1/lists` | Crear lista | Usuario autenticado |
| GET | `/api/v1/lists` | Listar mis listas | Dueño |
| GET · PATCH · DELETE | `/api/v1/lists/{list_id}` | Obtener, editar o eliminar la lista | Dueño |
| POST | `/api/v1/lists/{list_id}/tasks` | Crear tarea | Dueño |
| GET | `/api/v1/lists/{list_id}/tasks` | Listar tareas con filtros y completitud | Dueño |
| GET | `/api/v1/tasks/{task_id}` | Obtener tarea | Dueño o asignado |
| PATCH · DELETE | `/api/v1/tasks/{task_id}` | Editar o eliminar la tarea | Dueño |
| PUT | `/api/v1/tasks/{task_id}/status` | Cambiar el estado | Dueño o asignado |
| PUT · DELETE | `/api/v1/tasks/{task_id}/assignee` | Asignar o desasignar | Dueño |
| GET | `/api/v1/users/me/tasks` | Mis tareas asignadas | Asignado |

**Alternativas descartadas.**
- *Todo anidado (`/lists/{list_id}/tasks/{task_id}`)*: el `list_id` es redundante cuando el ID
  de la tarea ya es único, obliga a validar que ambos coincidan, y el asignado tendría que
  conocer una lista a la que no tiene acceso.
- *Sin versionado*: cualquier cambio incompatible rompería a los clientes existentes.

**Consecuencias.** El mismo endpoint de cambio de estado sirve al dueño y al asignado; la
autorización la resuelve el caso de uso.

---

## DEC-021 · Identificadores UUID v7 generados por el dominio

**Decisión.** Todas las entidades usan UUID versión 7 (`uuid.uuid7()`, biblioteca estándar desde
Python 3.14). El ID se asigna en el dominio al crear la entidad, no en la base de datos.

**Alternativas descartadas.**
- *Enteros autoincrementales*: con rutas planas, cualquiera puede recorrer `/tasks/1`,
  `/tasks/2`… y deducir cuántos recursos existen. Además, la entidad no tendría identidad hasta
  enviarse a la base de datos.
- *UUID v4*: totalmente aleatorio, fragmenta los índices B-tree. UUID v7 está ordenado por
  tiempo y se inserta al final del índice.

**Consecuencias.** Una entidad tiene identidad desde que se crea, como corresponde en DDD. El
proyecto requiere Python 3.14 o superior.

---

## DEC-022 · Edición parcial con PATCH

**Decisión.**
- Listas y tareas se editan con PATCH, enviando solo los campos que cambian.
- `entrypoints` usa `model_dump(exclude_unset=True)` para distinguir un campo ausente (no se
  modifica) de un campo enviado como `null` (se borra, si el campo es opcional; si es
  obligatorio, la petición se rechaza con 422).
- El caso de uso recibe los cambios como un `TypedDict` con `total=False` definido en
  `application` (p. ej. `TaskChanges`): cada clave es opcional y mypy verifica sus tipos.
- PATCH no modifica `status` ni `assignee`; tienen sus propias rutas (DEC-023).

**Alternativas descartadas.**
- *PUT*: reemplaza el recurso completo, así que el cliente tendría que reenviar todos los campos
  para cambiar uno.
- *Pasar al caso de uso el schema HTTP*: violaría DEC-012.
- *Pasar un `dict[str, Any]`*: mypy no podría verificarlo.

---

## DEC-023 · Estado y responsable como sub-recursos con PUT

**Decisión.**
- `PUT /tasks/{id}/status` con `{"status": "..."}` cambia el estado.
- `PUT /tasks/{id}/assignee` con `{"email": "..."}` asigna como responsable al usuario
  registrado con ese email; `DELETE /tasks/{id}/assignee` lo quita.
- El responsable es un campo de la tarea (`assignee_id`), no una entidad propia.
- Asignar al usuario que ya es responsable no hace nada y no reenvía el aviso.

**Alternativas descartadas.**
- *POST para asignar*: POST crea un recurso nuevo y no es idempotente; un reintento por timeout
  podría enviar dos avisos.
- *Asignar por `user_id`*: con UUID, el dueño no tiene forma de conocer el ID de otro usuario.
- *Endpoint de búsqueda de usuarios (`GET /users?email=`)*: agrega superficie y facilita
  recorrer la lista de usuarios registrados.
- *Historial de asignaciones (entidad `Assignment`)*: el enunciado pide "un usuario responsable"
  por tarea. Queda como posible extensión.

**Consecuencias.** Ambas operaciones son idempotentes, coherente con DEC-004: repetir el mismo
estado o el mismo responsable no tiene efecto, que es lo que PUT promete. Asignar por email
coincide con cómo funcionan las herramientas de tareas conocidas y con un aviso que se envía
por email. Como el registro (DEC-031), revela si un email está registrado.

---

## DEC-024 · Filtros, paginación, orden y forma del listado

**Decisión.**
- **Filtros:** `?status=` y `?priority=` aceptan un valor cada uno y se combinan con AND.
- **Paginación:** `limit` y `offset`; 10 elementos por defecto y 100 como máximo. Se aplica a
  todas las colecciones (`/lists`, `/lists/{id}/tasks`, `/users/me/tasks`).
- **Orden:** prioridad descendente, luego fecha de creación descendente y, como desempate, ID.
  El desempate garantiza un orden total, sin el cual la paginación por offset puede repetir u
  omitir elementos entre páginas.
- **Forma de la respuesta:**

```json
{
  "items": [],
  "pagination": { "limit": 10, "offset": 0, "total": 7 },
  "completion": { "total_tasks": 12, "completed_tasks": 5, "percentage": 41.67 }
}
```

- `pagination.total` cuenta las tareas que cumplen el filtro; `completion.total_tasks` cuenta
  todas las tareas de la lista (DEC-008). Se agrupan por separado para que no se confundan.
- `percentage` se expone como número (`float`) con dos decimales.

**Alternativas descartadas.**
- *Paginación por cursor*: conviene en colecciones enormes que cambian constantemente; una lista
  de tareas tiene decenas o cientos de elementos.
- *Sin paginación*: una colección sin límite crece sin control en el tamaño de la respuesta.

**Extensiones futuras.** Varios valores por filtro (combinados con OR dentro del mismo campo) y
orden configurable por el cliente.

---

## DEC-025 · Códigos de respuesta

**Decisión.**
- Crear: `201 Created`, con el recurso en el body y el header `Location` apuntando a él.
- Eliminar: `204 No Content`.
- Recurso inexistente (incluido eliminar algo ya eliminado): `404 Not Found`.

**Consecuencias.** Que un segundo DELETE devuelva 404 no contradice la idempotencia: esta se
refiere al estado del servidor, que es el mismo después del primer DELETE o del décimo.

---

## DEC-026 · 404 para lo que no se puede ver, 403 para lo que no se puede hacer

**Contexto.** Un usuario puede pedir un recurso que existe pero no le pertenece.

**Decisión.**
- Si el usuario **no puede ver** el recurso (p. ej. la lista de otro usuario), se responde
  `404 Not Found`, igual que si no existiera.
- Si el usuario **puede verlo** pero no tiene permiso para esa acción (p. ej. el asignado intenta
  editar o eliminar su tarea), se responde `403 Forbidden`.

**Alternativas descartadas.**
- *403 en todos los casos*: confirma la existencia del recurso a quien no debería saberla. Los
  UUID son difíciles de adivinar, pero se filtran en logs, URLs compartidas y capturas.
- *404 en todos los casos*: confunde al asignado, que acaba de ver la tarea con un GET.

**Consecuencias.** Sigue lo que permite la RFC 9110: un servidor que quiere ocultar la existencia
de un recurso prohibido puede responder 404.

---

## DEC-027 · Excepciones por categoría y un único handler

**Decisión.**
- Las excepciones se definen en `domain/exceptions.py`, organizadas en una jerarquía con una base
  `DomainError` y cinco categorías: `NotFoundError`, `PermissionDeniedError`, `ConflictError`,
  `BusinessRuleViolation` y `AuthenticationError`. Cada error concreto hereda de su categoría
  (p. ej. `TaskNotFound(NotFoundError)`).
- `entrypoints` registra un único handler para `DomainError`, que traduce la categoría a un
  código HTTP: 404, 403, 409, 422 y 401 respectivamente. Los 401 incluyen el header
  `WWW-Authenticate: Bearer`.
- La quinta categoría se agregó al implementar el login (DEC-045).
- Un handler de último recurso para cualquier otra excepción responde 500 con un mensaje
  genérico; la traza se registra solo en el log.

**Alternativas descartadas.**
- *Un handler por excepción concreta*: cada excepción nueva obliga a modificar `entrypoints`, y
  olvidar registrarla convierte el error en un 500.
- *Códigos HTTP dentro de las excepciones*: el dominio quedaría acoplado a HTTP.

**Consecuencias.** Agregar un error nuevo solo requiere heredar de la categoría correcta. El
dominio expresa qué pasó ("no existe", "conflicto"); `entrypoints` decide cómo se comunica.

---

## DEC-028 · Formato de error único basado en Problem Details (RFC 9457)

**Decisión.** Todas las respuestas de error, incluidas las de validación de Pydantic, usan el
mismo formato, con `Content-Type: application/problem+json`:

```json
{
  "title": "Validation error",
  "status": 422,
  "detail": "The request body contains invalid fields.",
  "code": "VALIDATION_ERROR",
  "errors": [{ "field": "title", "message": "String should have at most 200 characters" }]
}
```

- `title`, `status` y `detail` son los campos del estándar.
- `code` es un identificador estable para que lo procesen los clientes (`TASK_NOT_FOUND`).
- `errors` aparece solo en errores de validación, con el detalle por campo.
- El handler de `RequestValidationError` se reemplaza para producir este formato.

**Alternativas descartadas.**
- *El formato por defecto de FastAPI*: `{"detail": ...}` para unos errores y otra estructura
  para los de validación; el cliente tendría que manejar dos formatos.
- *Un formato propio*: no aporta nada sobre un estándar existente.

**Consecuencias.** Los clientes manejan todos los errores con la misma lógica y nunca dependen
del texto de `detail`, que es para personas y puede cambiar.

---

## DEC-029 · Cada capa valida lo que puede saber

**Decisión.**
- **Pydantic (`entrypoints`)**: forma y tipo de los datos. Mensajes por campo y documentación
  OpenAPI. Los schemas de entrada usan `extra="forbid"` para rechazar campos desconocidos.
- **Dominio**: las reglas que una entidad cumple siempre, venga de donde venga la llamada.
- **Caso de uso**: reglas que requieren consultar datos (existencia, unicidad, permisos).
- **Base de datos**: última línea de defensa (`UNIQUE`, claves foráneas, `CHECK`).

| Caso | Capa | HTTP |
|---|---|---|
| `title` de más de 200 caracteres | Pydantic y dominio | 422 |
| `title` vacío o con solo espacios | Dominio | 422 |
| `priority` con un valor inexistente | Pydantic | 422 |
| Crear una tarea enviando `status` | Pydantic (`extra="forbid"`) | 422 |
| Asignar a un usuario inexistente | Caso de uso (`AssigneeNotFound`) | 422 |
| Registrarse con un email ya usado | Caso de uso y `UNIQUE` | 409 |
| `limit` mayor que 100 | Pydantic | 422 |
| Crear una tarea en una lista ajena | Caso de uso | 404 (DEC-026) |

**Detalles.**
- Los límites (p. ej. `TITLE_MAX_LENGTH = 200`) se definen una sola vez en el dominio y los
  schemas de Pydantic los importan.
- Las tareas siempre se crean en `PENDING`; el schema de creación no acepta `status`.
- Un usuario inexistente en el body es 422 y no 404: el recurso de la URL sí existe.
- Dos registros simultáneos con el mismo email pasan ambos la verificación del caso de uso; el
  `UNIQUE` rechaza al segundo e `infrastructure` traduce ese error a `EmailAlreadyRegistered`.

**Alternativas descartadas.**
- *Validar solo con Pydantic*: un caso de uso invocado desde un script o una tarea programada
  podría crear entidades inválidas.
- *Ignorar los campos desconocidos (comportamiento por defecto de Pydantic)*: el cliente
  creería que un campo mal escrito o no permitido fue aceptado.

---

## DEC-030 · Autenticación con JWT

**Decisión.**
- `POST /api/v1/auth/login` recibe un formulario con `username` (el email) y `password`, y
  devuelve un access token.
- Tokens firmados con PyJWT y HS256. La clave secreta viene de una variable de entorno.
- El token contiene solo `sub` (ID del usuario), `iat` y `exp`. Expira a los 30 minutos
  (configurable). No hay refresh token.
- `get_current_user` valida el token y consulta al usuario en la base de datos en cada request.
- Un token ausente, inválido o expirado, o de un usuario que ya no existe, recibe `401` con el
  header `WWW-Authenticate: Bearer`.
- La generación y validación de tokens se implementa en `infrastructure` detrás del puerto
  `TokenService`.

**Alternativas descartadas.**
- *Login con body JSON*: coherente con el resto de la API, pero el botón "Authorize" de Swagger
  no podría iniciar sesión directamente; el evaluador tendría que copiar el token a mano.
- *`python-jose`*: mantenimiento irregular y vulnerabilidades conocidas. La documentación de
  FastAPI migró a PyJWT.
- *RS256*: firma asimétrica, útil cuando otros servicios verifican tokens sin poder emitirlos.
  Aquí un único servicio hace ambas cosas.
- *Refresh token*: requiere guardarlo, rotarlo y poder revocarlo, otro subsistema completo.
  Queda como pendiente.
- *Confiar en el token sin consultar la base de datos*: si el usuario ya no existe (p. ej. tras
  recrear la base de datos), la petición terminaría en un 500 por violación de clave foránea en
  lugar de un 401.

**Consecuencias.** Una consulta por clave primaria adicional por request. El token es legible
por cualquiera (está codificado, no cifrado), por eso no lleva datos personales.

---

## DEC-031 · Contraseñas

**Decisión.**
- Hash con Argon2id (`argon2-cffi`), detrás del puerto `PasswordHasher`.
- Entre 8 y 128 caracteres, sin reglas de composición.
- Un login fallido responde siempre `401` con el mismo mensaje, exista o no el email. Si el email
  no existe, igual se verifica la contraseña contra un hash ficticio para que el tiempo de
  respuesta no revele la diferencia.

**Alternativas descartadas.**
- *`passlib` con bcrypt*: `passlib` no publica versiones desde 2020 y es incompatible con
  versiones recientes de `bcrypt`. OWASP recomienda Argon2id como primera opción.
- *Reglas de composición (mayúsculas, símbolos)*: NIST SP 800-63B prioriza la longitud sobre la
  complejidad.

**Consecuencias.** El máximo de 128 caracteres evita que una contraseña enorme se use para
saturar el cálculo del hash. **Concesión consciente:** el registro responde 409 si el email ya
existe, lo que revela qué emails están registrados. Evitarlo requiere verificación por email al
registrarse, fuera del alcance.

---

## DEC-032 · Destinatarios del aviso de asignación

**Decisión.** Solo se avisa al nuevo responsable. No se envía aviso al desasignar, al reasignar
al mismo usuario (DEC-023) ni cuando el dueño se asigna una tarea a sí mismo.

**Consecuencias.** Nadie recibe un aviso de algo que acaba de hacer o que no cambió.

---

## DEC-033 · Notificación de mejor esfuerzo, con un puerto que expresa la intención

**Decisión.**
- El puerto es `TaskAssignmentNotifier.notify_assigned(task, assignee)`: el caso de uso declara
  qué ocurrió, no cómo se comunica.
- El adaptador actual arma el email (destinatario, asunto, cuerpo) y lo escribe en el log;
  visible con `docker compose logs api`.
- El caso de uso notifica después del commit (DEC-017). Si la notificación falla, el error se
  registra en el log y la asignación se mantiene: el cliente recibe la respuesta exitosa porque
  lo que pidió sí ocurrió.
- En los tests se usa un notificador en memoria que registra los avisos para verificarlos.

**Alternativas descartadas.**
- *Puerto `EmailSender`*: nombra la tecnología, no la intención. Cambiar el canal (Slack, push)
  obligaría a modificar el caso de uso.
- *Fallar la asignación si falla el aviso*: la asignación ya está guardada; responder error haría
  creer al cliente que no ocurrió.
- *`BackgroundTasks` de FastAPI*: es un objeto del framework y no puede llegar al caso de uso sin
  romper DEC-009. Con un adaptador que solo escribe en el log, no hay latencia que ocultar.

**Pendientes para producción.** Enviar en segundo plano (una cola de tareas) y garantizar que
ningún aviso se pierda con el patrón *outbox*.

---

## DEC-034 · Estrategia de testing

**Contexto.** El enunciado exige tests unitarios y de integración con pytest, un `pytest.ini` y
una cobertura mínima del 75%.

**Decisión.**

| Tipo | Ubicación | Qué prueba | Contra qué |
|---|---|---|---|
| Unitario | `tests/unit/domain` | Entidades y value objects | Python puro |
| Unitario | `tests/unit/application` | Casos de uso | Implementaciones falsas de los puertos (DEC-037) |
| Unitario | `tests/unit/infrastructure`, `tests/unit/entrypoints` | Adaptadores sin I/O (JWT, Argon2, notificador) y la tabla de códigos HTTP | Python puro |
| Integración | `tests/integration/repositories` | Filtros, orden, conteos, cascada, error de `UNIQUE` | PostgreSQL real |
| Integración | `tests/integration/api` | Códigos, formato de error, autenticación, permisos | `TestClient` y PostgreSQL real |

- La tabla de permisos de DEC-002 se prueba con un test parametrizado:
  (quién, acción) → código esperado.
- `pytest.ini` define `testpaths = tests`, los marcadores `unit` e `integration`, y
  `--strict-markers`.
- Cobertura con `--cov-branch --cov-report=term-missing --cov-fail-under=75`. Solo se excluyen
  las migraciones y los bloques `if TYPE_CHECKING:`.
- Los datos de prueba se crean con funciones simples (`make_task(**overrides)`).

**Alternativas descartadas.**
- *Cobertura solo por líneas*: no detecta ramas de un `if` que nunca se ejecutan.
- *`factory_boy`*: una dependencia más sin beneficio con entidades de clases normales.

**Consecuencias.** La mayor parte de la lógica se prueba en milisegundos sin base de datos. El
piso de 75% es el que exige el enunciado; la cobertura real se informa en el README.

---

## DEC-035 · Base de datos de tests en docker-compose

**Decisión.**
- Un servicio `db-test` de PostgreSQL que guarda sus datos en memoria (`tmpfs`).
- Un servicio `tests` construido con la etapa `test` del Dockerfile, que ejecuta pytest contra
  `db-test`.
- Ambos servicios pertenecen al perfil `test` de docker-compose, así que `docker compose up` no
  los levanta.
- Comando para el evaluador: `docker compose run --rm tests`.

**Alternativas descartadas.**
- *Testcontainers*: requiere Python 3.14 instalado en la máquina de quien ejecuta los tests, y
  correr los tests dentro de un contenedor exigiría darle acceso al Docker del host.
- *Usar la base de datos de desarrollo*: los tests dependerían de datos previos y los
  modificarían.

**Consecuencias.** Ejecutar los tests solo requiere Docker. En desarrollo local también se puede
levantar `db-test` y ejecutar pytest directamente.

---

## DEC-036 · Aislamiento de tests con `TRUNCATE`

**Decisión.** Después de cada test de integración se vacían todas las tablas con `TRUNCATE`.

**Alternativas descartadas.**
- *Transacción revertida al final de cada test (con savepoints)*: más rápida, pero requiere una
  configuración especial de SQLAlchemy para que los commits de los casos de uso (DEC-017) no
  cierren la transacción externa. Si queda mal configurada, los tests pasan sin probar lo que
  creen probar.

**Consecuencias.** Los commits de los tests son reales. Con tres tablas, el costo es de
milisegundos por test.

---

## DEC-037 · Implementaciones falsas en lugar de mocks

**Decisión.** Los tests unitarios de casos de uso usan implementaciones en memoria de los
puertos: `InMemoryTaskRepository`, un `FakeUnitOfWork` que registra si se hizo commit, un
notificador que guarda los avisos enviados y un reloj fijo.

**Alternativas descartadas.**
- *`unittest.mock`*: verifica qué métodos se llamaron, no qué resultado quedó. Un cambio interno
  que no altera el comportamiento rompería los tests.

**Consecuencias.** Las implementaciones falsas se escriben una vez y las reutilizan todos los
tests. Los tests verifican estado, no interacciones.

---

## DEC-038 · El tiempo es una dependencia explícita

**Contexto.** `completed_at` y la expiración del JWT dependen del momento actual.

**Decisión.**
- El dominio nunca llama a `datetime.now()`. Los métodos que necesitan el momento lo reciben
  como parámetro: `task.change_status(new_status, at=now)`.
- Los casos de uso obtienen el momento de un puerto `Clock`. En producción se usa el reloj del
  sistema; en los tests, un reloj fijo.

**Alternativas descartadas.**
- *Congelar el tiempo con una librería (`time-machine`, `freezegun`)*: no requiere cambios de
  diseño, pero manipula el reloj global del proceso y oculta que el dominio depende del tiempo.

**Consecuencias.** El dominio es determinista: el mismo input produce siempre el mismo
resultado. Es coherente con el resto del diseño: el reloj del sistema también es algo externo.

---

## DEC-039 · Python 3.14 y uv

**Decisión.**
- Python 3.14.
- Dependencias gestionadas con uv: `pyproject.toml` (estándar PEP 621) y `uv.lock`, que fija
  también las dependencias indirectas.

**Alternativas descartadas.**
- *Python 3.15*: todavía en *release candidate*; no todas las librerías publican binarios para
  esa versión.
- *Poetry*: más lento en la resolución e instalación.
- *pip con `requirements.txt`*: no fija las dependencias indirectas, así que dos instalaciones
  pueden terminar con versiones distintas.

**Consecuencias.** `uv sync` crea el entorno completo e incluso descarga Python 3.14 si no está
instalado. `uuid.uuid7()` está disponible en la biblioteca estándar (DEC-021).

---

## DEC-040 · Calidad de código: flake8, black, isort, mypy y pre-commit

**Decisión.**
- flake8 como linter, configurado en `.flake8`: `max-line-length = 88` y
  `extend-ignore = E203, E701, E704`, las reglas que contradicen el formato de black.
- black como formateador e isort con `profile = "black"`.
- mypy en modo estricto (DEC-010).
- pre-commit ejecuta las cuatro herramientas antes de cada commit, usando las versiones fijadas
  en `uv.lock`.

**Alternativas descartadas.**
- *ruff*: más rápido y podría reemplazar a flake8 e isort, pero el enunciado exige flake8 con su
  archivo `.flake8`. Tener ambos duplicaría reglas.

---

## DEC-041 · Integración continua con GitHub Actions

**Decisión.** En cada push y pull request se ejecutan black, isort, flake8, mypy y la suite de
tests con cobertura contra un PostgreSQL de servicio.

**Consecuencias.** El estado del repositorio es visible sin clonarlo.

---

## DEC-042 · Configuración por variables de entorno

**Decisión.**
- `pydantic-settings` en `infrastructure`, con dos clases: `DatabaseSettings`
  (`DATABASE_URL`) y `AuthSettings` (`JWT_SECRET_KEY`, `JWT_EXPIRE_MINUTES`).
- `.env.example` se versiona; `.env` lo ignora git.
- `JWT_SECRET_KEY` es obligatoria y debe tener al menos 32 caracteres: la aplicación no arranca
  sin ella.

**Alternativas descartadas.**
- *Una sola clase de configuración*: el servicio de migraciones necesitaría una clave JWT que no
  usa.
- *Valor por defecto para la clave JWT*: una clave conocida en el código es una clave pública.

---

## DEC-043 · Docker: tres etapas y perfiles de docker-compose

**Decisión.**
- `Dockerfile` con tres etapas:
  - `builder`: instala las dependencias de producción con uv.
  - `runtime`: `python:3.14-slim`, solo el entorno virtual y el código, usuario sin privilegios.
  - `test`: parte de `builder` y agrega las dependencias de desarrollo y los tests.
- `docker-compose.yml`:
  - `db` (`postgres:18` con *healthcheck*), `migrate` (DEC-018) y `api`.
  - `db-test` y `tests` en el perfil `test` (DEC-035).
- La API expone `GET /health` para que docker-compose sepa si está viva.

**Alternativas descartadas.**
- *Imagen `alpine`*: usa musl en lugar de glibc; algunas librerías compiladas tendrían que
  compilarse durante el build.
- *Una sola etapa*: la imagen final incluiría herramientas de build y dependencias de
  desarrollo.

**Consecuencias.** `docker compose up` levanta base de datos, migraciones y API;
`docker compose run --rm tests` ejecuta los tests. Ninguno de los dos requiere Python instalado.

---

## DEC-044 · Documentación, idioma y commits

**Decisión.**
- Código, mensajes de la API y commits en inglés; `README.md` y `DECISION_LOG.md` en español,
  el idioma del enunciado.
- Commits con Conventional Commits (`feat:`, `test:`, `chore:`, `docs:`).
- `Makefile` con atajos (`make up`, `make test`, `make lint`, `make format`); el README muestra
  también los comandos completos para quien no tenga `make`.

---

## DEC-045 · Ajustes durante la implementación

Decisiones menores que surgieron al escribir el código, dentro del marco de las anteriores.

| Ajuste | Motivo |
|---|---|
| El value object `Email` normaliza el valor (espacios y minúsculas). | `Ana@X.com` y `ana@x.com` son el mismo usuario: la unicidad del email no debe depender de mayúsculas. |
| Nueva categoría de error `AuthenticationError` → 401 (DEC-027). | El login fallido y el token inválido no encajaban en las cuatro categorías originales. |
| Los objetos de entrada y salida de `application` (`Page`, `TaskFilters`, `TaskListing`) son `dataclass(frozen=True)`. | No protegen reglas, solo transportan datos; DEC-010 descartó las dataclasses para las **entidades** por el encapsulamiento, que aquí no aplica. |
| `Priority` es un `StrEnum` con una propiedad `rank`. | La API expone el nombre (`"HIGH"`) y la base de datos guarda `rank` (DEC-019) sin una segunda enumeración. |
| La expiración del JWT se valida contra el `Clock` inyectado, no contra el reloj interno de PyJWT. | Coherente con DEC-038: los tests de expiración son deterministas. |
| El verificador de contraseñas solo traduce `VerifyMismatchError` a "no coincide". | Un hash corrupto en la base de datos es un error del servidor (500), no unas credenciales inválidas. |
| El registro responde 201 sin header `Location` (excepción a DEC-025). | No existe un endpoint `GET /users/{id}` al que apuntar. |
| Los tests usan `httpx2` como cliente del `TestClient`. | Starlette 1.x marcó `httpx` como obsoleto para el `TestClient`. |
| El paquete incluye `py.typed` y mypy usa el plugin de Pydantic. | Los schemas se verifican con sus tipos reales y el paquete se puede analizar desde otros módulos (p. ej. las migraciones). |

---

## Pendientes y extensiones futuras

Lo que quedó fuera del alcance, con la decisión que lo menciona:

| Pendiente | Origen |
|---|---|
| Refresh tokens y revocación de tokens | DEC-030 |
| Verificación del email al registrarse (evitaría revelar emails registrados) | DEC-031 |
| Límite de intentos de login (protección contra fuerza bruta) | DEC-031 |
| Envío de avisos en segundo plano y patrón *outbox* | DEC-033 |
| Historial de asignaciones | DEC-023 |
| Varios valores por filtro (OR dentro del campo) y orden configurable | DEC-024 |
| Listas compartidas con miembros | DEC-002 |
| Restringir transiciones de estado si el negocio lo pidiera | DEC-004 |
| Contadores desnormalizados si el cálculo de completitud se volviera costoso | DEC-008 |
| Acceso asíncrono a la base de datos si la concurrencia lo exigiera | DEC-015 |
