# Rincón Lector · Tótem físico (Wokwi)

ESP32 programado en Arduino que funciona como el tótem físico del Rincón Lector.
Se comunica con la app de Streamlit por MQTT (broker público `broker.hivemq.com`, puerto 1883).

**Simulación en Wokwi:** https://wokwi.com/projects/481061636688423937

## Archivos

| Archivo | Qué es |
|---|---|
| `sketch.ino` | Firmware en Arduino (WiFi, MQTT, LCD, LED RGB, lámpara, buzzer, botón y LDR) |
| `diagram.json` | Circuito de Wokwi |
| `libraries.txt` | Librerías: PubSubClient y LiquidCrystal I2C |

## Componentes y pines

| Componente | Pin ESP32 | Función |
|---|---|---|
| LCD 16x2 I2C (0x27) | SDA 21 · SCL 22 · 5V · GND | Muestra el título (con desplazamiento) y el idioma/género |
| LED RGB (cátodo común) | R 25 · G 26 · B 27 (con 220 Ω) | Color del género: morado = filosofía, rojo = distopía |
| Botón "Léemelo" | 4 (INPUT_PULLUP) · GND | Le pide a la app leer el resumen en voz alta |
| Sensor de luz (LDR, salida AO) | 34 · 3V3 · GND | Mide la luz ambiente de la mesa de lectura |
| LED lámpara (amarillo) | 18 (PWM, con 220 Ω) | Lámpara de lectura con brillo regulable |
| Buzzer | 19 · GND | Pitido al presionar el botón y melodía de "libro terminado" |

## Tópicos MQTT

| Tópico | Dirección | Mensaje | Ejemplo |
|---|---|---|---|
| `rinconlector_mac/libro` | App → ESP32 | `titulo\|genero\|idioma` o `ninguno` | `El lobo estepario\|filosofia\|es` |
| `rinconlector_mac/lampara` | App → ESP32 | brillo de 0 a 100 | `80` |
| `rinconlector_mac/fin` | App → ESP32 | `tocar` | `tocar` |
| `rinconlector_mac/boton` | ESP32 → App | `leer` | `leer` |
| `rinconlector_mac/luz` | ESP32 → App | luz de 0 a 100 (cada 2 s) | `76` |

## Pruebas realizadas (18 nov 2026)

| Prueba | Resultado |
|---|---|
| Compilación en Wokwi | ✅ Sin errores |
| Conexión WiFi (Wokwi-GUEST) y MQTT | ✅ Conectado |
| Envío de *The Ballad of Songbirds and Snakes* (EN) | ✅ Título desplazándose, "EN Dystopia", LED rojo |
| Envío de *El lobo estepario* (ES) | ✅ "ES Filosofia", LED morado |
| Lámpara al 80 % y al 30 % | ✅ Cambia el brillo |
| Melodía de libro terminado | ✅ Suena |
| Botón "Léemelo" → app | ✅ Llega `leer` |
| Sensor de luz → app | ✅ Llega el nivel cada 2 s |

> Nota: si la simulación corre por debajo del 100 % de velocidad, los mensajes pueden tardar unos segundos en procesarse.
> Para probar el WiFi del simulador hay que tener sesión iniciada en Wokwi.
