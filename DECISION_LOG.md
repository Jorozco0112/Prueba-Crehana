# Decision Log

Registro de las decisiones técnicas del proyecto. Cada entrada sigue el formato:
**Contexto** → **Decisión** → **Alternativas descartadas** → **Consecuencias**.

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
- El cambio pasa siempre por `Task.change_status()`. Al pasar a `COMPLETED` se registra
  `completed_at`; al salir de `COMPLETED` se borra.
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

**Consecuencias.** Las tareas pueden ordenarse por importancia real.

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
`UserRepository`) y de servicios externos (`EmailSender`, `PasswordHasher`, `TokenService`) se
definen en `application` como clases abstractas (`ABC`).

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
  dependencias de todos sus métodos (cambiar el estado cargaría con el `EmailSender` de la
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
