/*
  ============================================================
   RINCÓN LECTOR - Tótem físico (ESP32 programado en Arduino)
   Proyecto final - Interfaces Multimodales
  ============================================================
   Se comunica con la app de Streamlit por MQTT (broker.hivemq.com)

   App -> ESP32
     rinconlector_mac/libro    "titulo|genero|idioma"  (ej: "El lobo estepario|filosofia|es")
                               "ninguno"               (apaga LED y vuelve al mensaje de inicio)
     rinconlector_mac/lampara  "0" a "100"             (brillo de la lámpara de lectura)
     rinconlector_mac/fin      "tocar"                 (melodía de libro terminado)

   ESP32 -> App
     rinconlector_mac/boton    "leer"                  (botón "Léemelo" presionado)
     rinconlector_mac/luz      "0" a "100"             (luz ambiente medida por el LDR, cada 2 s)
  ============================================================
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ---------- WiFi y MQTT ----------
const char* WIFI_SSID   = "Wokwi-GUEST";
const char* WIFI_PASS   = "";
const char* MQTT_BROKER = "broker.hivemq.com";
const int   MQTT_PORT   = 1883;

const char* TOPIC_LIBRO   = "rinconlector_mac/libro";
const char* TOPIC_LAMPARA = "rinconlector_mac/lampara";
const char* TOPIC_FIN     = "rinconlector_mac/fin";
const char* TOPIC_BOTON   = "rinconlector_mac/boton";
const char* TOPIC_LUZ     = "rinconlector_mac/luz";

// ---------- Pines ----------
const int PIN_LED_R   = 25;   // LED RGB - rojo
const int PIN_LED_G   = 26;   // LED RGB - verde
const int PIN_LED_B   = 27;   // LED RGB - azul
const int PIN_BOTON   = 4;    // Botón "Léemelo"
const int PIN_LDR     = 34;   // Sensor de luz (salida analógica AO)
const int PIN_LAMPARA = 18;   // LED de la lámpara de lectura
const int PIN_BUZZER  = 19;   // Buzzer

// ---------- Objetos ----------
WiFiClient espClient;
PubSubClient mqtt(espClient);
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ---------- Estado ----------
String titulo = "";            // título que se muestra en la LCD
String linea2 = "";            // segunda línea (idioma y género)
int    posScroll = 0;          // posición del desplazamiento del título
unsigned long ultimoScroll = 0;
unsigned long ultimaLuz = 0;
int    estadoBotonAnterior = HIGH;
unsigned long ultimoCambioBoton = 0;
bool   tocarMelodia = false;   // se activa al recibir "tocar"

// ============================================================
//  Utilidades
// ============================================================

// Prende el LED RGB con el color indicado (0-255 por canal)
void colorLED(int r, int g, int b) {
  analogWrite(PIN_LED_R, r);
  analogWrite(PIN_LED_G, g);
  analogWrite(PIN_LED_B, b);
}

// Escribe un texto en una línea de la LCD, rellenando con espacios
void escribirLinea(int fila, String texto) {
  while (texto.length() < 16) texto += " ";
  lcd.setCursor(0, fila);
  lcd.print(texto.substring(0, 16));
}

// Pantalla de bienvenida (sin libro)
void pantallaInicio() {
  titulo = "";
  posScroll = 0;
  escribirLinea(0, "  Rincon Lector");
  escribirLinea(1, "Muestra un libro");
  colorLED(0, 0, 0);
}

// Melodía corta de "¡libro terminado!"
void melodiaFin() {
  int notas[]    = {523, 659, 784, 1047, 784, 1047};
  int duracion[] = {150, 150, 150, 300,  150, 450};
  for (int i = 0; i < 6; i++) {
    tone(PIN_BUZZER, notas[i], duracion[i]);
    delay(duracion[i] + 40);
  }
  noTone(PIN_BUZZER);
}

// Muestra el libro reconocido: título, idioma, género y color
void mostrarLibro(String mensaje) {
  int sep1 = mensaje.indexOf('|');
  int sep2 = mensaje.indexOf('|', sep1 + 1);

  String nuevoTitulo = (sep1 > 0) ? mensaje.substring(0, sep1) : mensaje;
  String genero = (sep1 > 0) ? mensaje.substring(sep1 + 1, (sep2 > 0) ? sep2 : mensaje.length()) : "";
  String idioma = (sep2 > 0) ? mensaje.substring(sep2 + 1) : "es";
  genero.toLowerCase();
  idioma.toLowerCase();

  // Color según el género del libro
  String nombreGenero;
  if (genero == "filosofia") {
    colorLED(150, 0, 255);                       // morado
    nombreGenero = (idioma == "en") ? "Philosophy" : "Filosofia";
  } else if (genero == "distopia") {
    colorLED(255, 0, 0);                         // rojo
    nombreGenero = (idioma == "en") ? "Dystopia" : "Distopia";
  } else {
    colorLED(255, 255, 255);                     // blanco: otro género
    nombreGenero = genero;
  }

  titulo = nuevoTitulo;
  posScroll = 0;
  linea2 = ((idioma == "en") ? "EN " : "ES ") + nombreGenero;

  escribirLinea(0, titulo);
  escribirLinea(1, linea2);
}

// Desplaza el título si no cabe en los 16 caracteres
void actualizarScroll() {
  if (titulo.length() <= 16) return;
  if (millis() - ultimoScroll < 400) return;
  ultimoScroll = millis();

  String texto = titulo + "   ";
  String ventana = "";
  for (int i = 0; i < 16; i++) {
    ventana += texto[(posScroll + i) % texto.length()];
  }
  escribirLinea(0, ventana);
  posScroll = (posScroll + 1) % texto.length();
}

// ============================================================
//  MQTT: mensajes que llegan desde la app
// ============================================================
void alRecibirMensaje(char* topic, byte* payload, unsigned int length) {
  String mensaje = "";
  for (unsigned int i = 0; i < length; i++) mensaje += (char)payload[i];
  mensaje.trim();

  Serial.print("Mensaje en ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(mensaje);

  String t = String(topic);

  if (t == TOPIC_LIBRO) {
    if (mensaje == "ninguno" || mensaje.length() == 0) pantallaInicio();
    else mostrarLibro(mensaje);
  }
  else if (t == TOPIC_LAMPARA) {
    int nivel = constrain(mensaje.toInt(), 0, 100);
    analogWrite(PIN_LAMPARA, map(nivel, 0, 100, 0, 255));
    Serial.print("Lampara al ");
    Serial.print(nivel);
    Serial.println("%");
  }
  else if (t == TOPIC_FIN) {
    if (mensaje == "tocar") tocarMelodia = true;   // se toca en el loop
  }
}

// ============================================================
//  Conexiones
// ============================================================
void conectarWiFi() {
  escribirLinea(0, "  Rincon Lector");
  escribirLinea(1, "Conectando WiFi");
  Serial.print("Conectando a WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS, 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  Serial.println(" listo!");
}

void conectarMQTT() {
  while (!mqtt.connected()) {
    escribirLinea(1, "Conectando MQTT");
    Serial.print("Conectando a MQTT... ");
    String clientId = "rinconlector-esp32-" + String(random(0xffff), HEX);
    if (mqtt.connect(clientId.c_str())) {
      Serial.println("conectado!");
      mqtt.subscribe(TOPIC_LIBRO);
      mqtt.subscribe(TOPIC_LAMPARA);
      mqtt.subscribe(TOPIC_FIN);
      pantallaInicio();
    } else {
      Serial.print("fallo, rc=");
      Serial.print(mqtt.state());
      Serial.println(" - reintento en 2 s");
      delay(2000);
    }
  }
}

// ============================================================
//  Setup y loop
// ============================================================
void setup() {
  Serial.begin(115200);

  pinMode(PIN_LED_R, OUTPUT);
  pinMode(PIN_LED_G, OUTPUT);
  pinMode(PIN_LED_B, OUTPUT);
  pinMode(PIN_LAMPARA, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_BOTON, INPUT_PULLUP);

  colorLED(0, 0, 0);
  analogWrite(PIN_LAMPARA, 0);

  lcd.init();
  lcd.backlight();

  randomSeed(micros());
  conectarWiFi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(alRecibirMensaje);
  conectarMQTT();
}

void loop() {
  if (!mqtt.connected()) conectarMQTT();
  mqtt.loop();

  // --- Botón "Léemelo" (con antirrebote) ---
  int estadoBoton = digitalRead(PIN_BOTON);
  if (estadoBoton != estadoBotonAnterior && millis() - ultimoCambioBoton > 50) {
    ultimoCambioBoton = millis();
    if (estadoBoton == LOW) {
      mqtt.publish(TOPIC_BOTON, "leer");
      Serial.println("Boton presionado -> leer");
      tone(PIN_BUZZER, 880, 80);   // pitido corto de confirmación
    }
    estadoBotonAnterior = estadoBoton;
  }

  // --- Sensor de luz: se envía cada 2 segundos ---
  if (millis() - ultimaLuz > 2000) {
    ultimaLuz = millis();
    int lectura = analogRead(PIN_LDR);               // 0 (mucha luz) a 4095 (oscuro)
    int luz = map(lectura, 0, 4095, 100, 0);         // 100 = mucha luz, 0 = oscuro
    luz = constrain(luz, 0, 100);
    mqtt.publish(TOPIC_LUZ, String(luz).c_str());
  }

  // --- Melodía de libro terminado ---
  if (tocarMelodia) {
    tocarMelodia = false;
    melodiaFin();
  }

  // --- Desplazamiento del título largo ---
  actualizarScroll();
}
