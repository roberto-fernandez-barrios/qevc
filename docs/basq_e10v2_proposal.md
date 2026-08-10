# Solicitud de acceso BasQ — Workload E10 v2 (estimación conservadora)

**Proyecto:** *When Can Quantum Event Classifiers Be Trusted? Conditional
Validity under Collider Systematics* (paper Q1 en preparación; E00–E11
completados en simulación + una validación de hardware preliminar).
**Solicitante:** Roberto Fernández Barrios.
**Backend objetivo:** `ibm_basquecountry` (IBM Quantum System Two, procesador
**Heron r2, 156 qubits**, BasQ – San Sebastián).

---

## 1. Contexto y valor científico

El proyecto ha demostrado (E09, simulación; E10 v1, hardware IBM Cloud) que:

- el error de estimación del kernel cuántico escala como 1/√shots
  (13,7% → 2,4% Frobenius entre 128 y 4.096 shots);
- en hardware real (`ibm_marrakesh`, Heron r2, 496 circuitos × 2.048 shots),
  el **ruido de dispositivo domina el presupuesto de error ~8×** sobre el
  ruido puro de shots (17,0% vs 1,9% Frobenius a igual presupuesto);
- los certificados de validez solo se desestabilizan cerca de las fronteras
  de decisión (8/360 flips), pero esa conclusión procede de kernels con
  ruido *simulado*.

**E10 v2 responde la pregunta que queda abierta:** ¿sobrevive el *pipeline
completo de certificación* (entrenamiento + scoring + auditoría fail-closed)
cuando el kernel procede íntegramente de hardware real, y qué fracción del
exceso de ruido de dispositivo es recuperable con mitigación estándar? Es el
mínimo experimento que convierte la sección "Quantum Realism" del paper de
una comparación a nivel de kernel en una validación del framework completo.

## 2. Diseño experimental mínimo (3 niveles, valor decreciente)

Feature map congelado del estudio principal (8 qubits, ZZ-map, 2
repeticiones, entanglement lineal, bandwidth 0,5; hiperparámetros
predeclarados — sin ajuste en hardware). Protocolo compute–uncompute;
entrada del Gram = frecuencia del resultado |0…0⟩; counts crudos archivados;
provenance completa (calibración, mapeo de qubits, timestamps, job ids).

| Nivel | Contenido | Circuitos | Shots/circ. | Pregunta que responde |
|---|---|---|---|---|
| **T1a** | Gram de entrenamiento crudo, n=96 eventos (96·95/2) | 4.560 | 4.096 | exceso de ruido de dispositivo a escala entrenable |
| **T1b** | Mismo Gram con mitigación (dynamical decoupling + Pauli twirling, mismo total de shots) | 4.560 | 4.096 | fracción recuperable del exceso (~15% en v1) |
| **T2** | Cross-Gram de despliegue 96×64 (64 eventos de test, crudo) | 6.144 | 4.096 | pipeline completo: QK-SVC entrenado y desplegado sobre kernels 100% hardware + auditoría de claims |
| **T3** | Sub-Gram de deriva, 24 eventos (276 pares) × 3 sesiones en días distintos | 828 | 4.096 | deriva de calibración como "entorno" adicional (conecta con la tesis de shift del paper) |

Total: **16.092 circuitos × 4.096 shots ≈ 65,9 M shots.**

## 3. Parámetros técnicos estimados

| Parámetro | Valor | Base de la estimación |
|---|---|---|
| Qubits utilizados | **8** (cadena lineal; se elige la cadena de mejor fidelidad de la calibración del día) | diseño del feature map (D-011) |
| Profundidad post-transpilación | **~180–190** (mediana 182 medida) | job real `d9t2jrvtfhrs73dtd8dg` en `ibm_marrakesh` (Heron r2, misma generación), `optimization_level=1`; con nivel 3 se espera ~10–15% menos |
| Puertas de 2 qubits por circuito | **~54** | ídem (medido) |
| Shots por circuito | **4.096** | E09: ≥2k necesarios; 4.096 baja el suelo de shots a σ≈0,008/entrada para aislar limpiamente la mitigación |
| Nº de circuitos (fidelidades) | **16.092** (4.560+4.560+6.144+828) | tabla §2 |
| Nº de configuraciones | **4** (crudo / mitigado / cross / deriva×3 sesiones) | tabla §2 |

## 4. Tiempo de QPU estimado (conservador, anclado en medida real)

**Ancla empírica:** el job v1 consumió **276 s de QPU** para 496 circuitos ×
2.048 shots (⇒ ~0,556 s/circuito a 2.048 shots, ~3.680 shots/s efectivos,
overhead de readout/reset incluido). Escalado lineal en shots ⇒ ~1,11
s/circuito a 4.096 shots.

| Nivel | Circuitos | Tiempo estimado |
|---|---|---|
| T1a | 4.560 | ~1,41 h |
| T1b | 4.560 | ~1,41 h (twirling: 32 aleatorizaciones × 128 shots = mismo total) |
| T2 | 6.144 | ~1,90 h |
| T3 | 828 | ~0,26 h (repartido en 3 sesiones) |
| **Subtotal** | 16.092 | **~4,97 h** |
| Contingencia (25%: variación de calibración, recompilación, algún re-run) | | ~1,25 h |
| **Solicitud total** | | **6,25 h de QPU** (redondeo: **6,5 h**) |

**Mínimo viable si el acceso es menor:** T1a+T1b = **~3,6 h con
contingencia** (responde la pregunta de mitigación); T2 y T3 son
prescindibles en ese orden. Con 2.048 shots todo se divide ≈ entre 2
(fallback documentado; el coste científico es un suelo de shots 1,4× mayor).

Notas operativas: jobs por lotes de ≤2.000 circuitos en modo Batch/Session;
T3 requiere 3 ventanas en días distintos (≈5 min cada una); el resto es
insensible al calendario. Sin requisitos de software especiales
(Qiskit + SamplerV2; todo el stack es reproducible desde el repositorio del
proyecto con manifiestos por run).

## 5. Compromiso de publicación

Los datos crudos (counts), la provenance completa y el código de análisis se
publicarán con el paper (repositorio con DOI); `ibm_basquecountry` y BasQ
serán acreditados según sus directrices. Los resultados negativos (p. ej.,
mitigación con ganancia marginal) se publican igualmente — el diseño del
estudio no depende de un resultado favorable.
