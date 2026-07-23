/**
 * RBC-bn — Robot Block Chaser (4-wheel mecanum)
 * ESP32 DevKit V1 firmware: nhận lệnh UART từ Raspberry Pi 5
 *
 * Protocol (từ Pi → ESP32):
 *   [0xBB] [CMD 1B] [SPEED_L 1B] [SPEED_R 1B] [CKSUM 1B] [0xCC]
 *
 *   CMD:
 *     0x01 = FORWARD        0x02 = BACKWARD
 *     0x03 = LEFT (strafe)  0x04 = RIGHT (strafe)
 *     0x05 = STOP           0x06 = ROTATE_LEFT
 *     0x07 = ROTATE_RIGHT
 *
 * Mecanum kinematics:
 *   V_fl = V_y + V_x + ω    V_fr = V_y - V_x - ω
 *   V_rl = V_y - V_x + ω    V_rr = V_y + V_x - ω
 *
 * ============================================================
 * HARDWARE PINNING
 * ============================================================
 *
 * BOARD: ESP32 DevKit V1
 *
 * UART (Pi 5 ↔ ESP32):
 *   ESP32 RX : GPIO16  ← Pi 5 TX
 *   ESP32 TX : GPIO17  → Pi 5 RX
 *
 * I2C (PCA9685 Servo Driver):
 *   SDA : GPIO21
 *   SCL : GPIO22
 *
 * L298N #1 — Mecanum Front:
 *   Motor A (FL): IN1=GPIO13  IN2=GPIO12
 *   Motor B (FR): IN3=GPIO14  IN4=GPIO27
 *
 * L298N #2 — Mecanum Rear:
 *   Motor A (RL): IN1=GPIO26  IN2=GPIO25
 *   Motor B (RR): IN3=GPIO33  IN4=GPIO32
 *
 * L298N #3 — spare (future expansion):
 *   Motor A: IN1=GPIO18  IN2=GPIO19
 *   Motor B: IN3=GPIO23  IN4=GPIO5
 *
 * PCA9685 — 16 servo channels (0-15)
 *
 * LƯU Ý: EN pins của L298N phải được jumper lên 5V (always enabled).
 *        PWM speed control dùng trực tiếp trên IN pins.
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// ============================================================
// PCA9685 Servo Driver
// ============================================================
#define PCA9685_ADDR  0x40
#define PCA9685_FREQ  50      // 50 Hz cho servo
#define SERVO_MIN    150      // ~0°  (pulse = 150/4096 * 20ms ≈ 0.73ms)
#define SERVO_MAX    600      // ~180° (pulse = 600/4096 * 20ms ≈ 2.93ms)

Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(PCA9685_ADDR);

// ============================================================
// L298N Motor Driver pin definitions
// ============================================================

// --- L298N #1: Front wheels ---
// Motor A → Front-Left (FL)
#define FL_IN1  13
#define FL_IN2  12
// Motor B → Front-Right (FR)
#define FR_IN1  14
#define FR_IN2  27

// --- L298N #2: Rear wheels ---
// Motor A → Rear-Left (RL)
#define RL_IN1  26
#define RL_IN2  25
// Motor B → Rear-Right (RR)
#define RR_IN1  33
#define RR_IN2  32

// --- L298N #3: Spare (unused) ---
// Motor A: IN1=18 IN2=19
// Motor B: IN3=23 IN4=5

// ============================================================
// PWM settings (ESP32 LEDC — pin-based API, core 3.x)
// ============================================================
#define PWM_FREQ       5000    // 5 kHz
#define PWM_RESOLUTION 8       // 0-255

// ============================================================
// UART / Protocol
// ============================================================
#define UART_BAUD      115200
#define FRAME_START    0xBB
#define FRAME_END      0xCC

#define CMD_FORWARD      0x01
#define CMD_BACKWARD     0x02
#define CMD_LEFT         0x03
#define CMD_RIGHT        0x04
#define CMD_STOP         0x05
#define CMD_ROTATE_LEFT  0x06
#define CMD_ROTATE_RIGHT 0x07

#define CMD_TIMEOUT_MS   500   // Auto-stop sau 500ms không nhận lệnh

// ============================================================
// State
// ============================================================
static uint8_t  g_cmd      = CMD_STOP;
static uint8_t  g_speed_l  = 0;
static uint8_t  g_speed_r  = 0;
static uint32_t g_last_cmd = 0;

// ============================================================
// Motor helpers — L298N: PWM on IN1 (forward) or IN2 (backward)
// EN pins jumpered to 5V (always on)
// ============================================================

void motor_init() {
    // Direction pins as outputs (PWM auto-attached in motor_set)
    pinMode(FL_IN1, OUTPUT); pinMode(FL_IN2, OUTPUT);
    pinMode(FR_IN1, OUTPUT); pinMode(FR_IN2, OUTPUT);
    pinMode(RL_IN1, OUTPUT); pinMode(RL_IN2, OUTPUT);
    pinMode(RR_IN1, OUTPUT); pinMode(RR_IN2, OUTPUT);

    motor_stop_all();
}

/**
 * L298N motor_set for IN-pin PWM (no separate EN).
 * ESP32 core 3.x API: ledcAttach(pin, freq, res), ledcWrite(pin, duty), ledcDetach(pin).
 *
 * Forward:  detach IN2, attach IN1, IN2=LOW, write speed to IN1
 * Backward: detach IN1, attach IN2, IN1=LOW, write speed to IN2
 * Stop:     detach both, set both LOW
 */
void motor_set(int in1, int in2, int speed) {
    int abs_speed = constrain(abs(speed), 0, 255);

    if (speed > 0) {
        // Forward: PWM → IN1, IN2 = LOW
        ledcDetach(in2);
        digitalWrite(in2, LOW);
        ledcAttach(in1, PWM_FREQ, PWM_RESOLUTION);
        ledcWrite(in1, abs_speed);
    } else if (speed < 0) {
        // Backward: PWM → IN2, IN1 = LOW
        ledcDetach(in1);
        digitalWrite(in1, LOW);
        ledcAttach(in2, PWM_FREQ, PWM_RESOLUTION);
        ledcWrite(in2, abs_speed);
    } else {
        // Stop: detach PWM from both, both LOW
        ledcDetach(in1);
        ledcDetach(in2);
        digitalWrite(in1, LOW);
        digitalWrite(in2, LOW);
    }
}

void motor_stop_all() {
    // Detach all PWM from motor pins
    ledcDetach(FL_IN1); ledcDetach(FL_IN2);
    ledcDetach(FR_IN1); ledcDetach(FR_IN2);
    ledcDetach(RL_IN1); ledcDetach(RL_IN2);
    ledcDetach(RR_IN1); ledcDetach(RR_IN2);

    // Set all IN pins LOW
    digitalWrite(FL_IN1, LOW); digitalWrite(FL_IN2, LOW);
    digitalWrite(FR_IN1, LOW); digitalWrite(FR_IN2, LOW);
    digitalWrite(RL_IN1, LOW); digitalWrite(RL_IN2, LOW);
    digitalWrite(RR_IN1, LOW); digitalWrite(RR_IN2, LOW);
}

// ============================================================
// Mecanum kinematics
// ============================================================

/**
 * Mecanum drive:
 *   Vx = strafe (dương = right), Vy = forward (dương = forward),
 *   ω = rotation (dương = CCW)
 *
 *   FL = Vy + Vx + ω     FR = Vy - Vx - ω
 *   RL = Vy - Vx + ω     RR = Vy + Vx - ω
 */
void mecanum_drive(int vx, int vy, int omega) {
    int fl = vy + vx + omega;
    int fr = vy - vx - omega;
    int rl = vy - vx + omega;
    int rr = vy + vx - omega;

    motor_set(FL_IN1, FL_IN2, fl);
    motor_set(FR_IN1, FR_IN2, fr);
    motor_set(RL_IN1, RL_IN2, rl);
    motor_set(RR_IN1, RR_IN2, rr);
}

// ============================================================
// Command handler
// ============================================================

void execute_cmd(uint8_t cmd, uint8_t speed_l, uint8_t speed_r) {
    int s = (int)constrain(speed_l, 0, 255);

    switch (cmd) {
        case CMD_FORWARD:
            mecanum_drive(0, s, 0);
            break;
        case CMD_BACKWARD:
            mecanum_drive(0, -s, 0);
            break;
        case CMD_LEFT:
            mecanum_drive(-s, 0, 0);
            break;
        case CMD_RIGHT:
            mecanum_drive(s, 0, 0);
            break;
        case CMD_STOP:
            mecanum_drive(0, 0, 0);
            break;
        case CMD_ROTATE_LEFT:
            mecanum_drive(0, 0, s);
            break;
        case CMD_ROTATE_RIGHT:
            mecanum_drive(0, 0, -s);
            break;
        default:
            mecanum_drive(0, 0, 0);
            break;
    }
}

// ============================================================
// UART parser — state machine
// ============================================================

enum ParseState { WAIT_START, READ_CMD, READ_SPL, READ_SPR, READ_CKSUM, WAIT_END };

static ParseState parse_state = WAIT_START;
static uint8_t    parse_cmd   = 0;
static uint8_t    parse_spl   = 0;
static uint8_t    parse_spr   = 0;
static uint8_t    parse_cksum = 0;

void uart_parse_byte(uint8_t b) {
    switch (parse_state) {
        case WAIT_START:
            if (b == FRAME_START) {
                parse_state = READ_CMD;
            }
            break;
        case READ_CMD:
            parse_cmd   = b;
            parse_state = READ_SPL;
            break;
        case READ_SPL:
            parse_spl   = b;
            parse_state = READ_SPR;
            break;
        case READ_SPR:
            parse_spr   = b;
            parse_state = READ_CKSUM;
            break;
        case READ_CKSUM: {
            uint8_t calc = (parse_cmd + parse_spl + parse_spr) & 0xFF;
            parse_cksum = b;
            if (calc == parse_cksum) {
                parse_state = WAIT_END;
            } else {
                parse_state = WAIT_START;  // checksum fail → discard
            }
            break;
        }
        case WAIT_END:
            if (b == FRAME_END) {
                g_cmd      = parse_cmd;
                g_speed_l  = parse_spl;
                g_speed_r  = parse_spr;
                g_last_cmd = millis();
            }
            parse_state = WAIT_START;
            break;
    }
}

// ============================================================
// PCA9685 Servo helpers
// ============================================================

void servo_init() {
    pca.begin();
    pca.setPWMFreq(PCA9685_FREQ);
    delay(10);
}

void servo_write(uint8_t channel, uint16_t pulse) {
    // pulse: SERVO_MIN (150) ~ SERVO_MAX (600) → 0° ~ 180°
    uint16_t p = constrain(pulse, SERVO_MIN, SERVO_MAX);
    pca.setPWM(channel, 0, p);
}

void servo_angle(uint8_t channel, uint8_t angle_deg) {
    // angle_deg: 0-180
    uint16_t pulse = map(constrain(angle_deg, 0, 180), 0, 180, SERVO_MIN, SERVO_MAX);
    pca.setPWM(channel, 0, pulse);
}

void servo_stop_all() {
    for (uint8_t ch = 0; ch < 16; ch++) {
        pca.setPWM(ch, 0, 0);
    }
}

// ============================================================
// Setup / Loop
// ============================================================

void setup() {
    // UART: Serial2 = Pi 5 UART (RX=GPIO16, TX=GPIO17)
    // Serial = USB monitor (debug only)
    Serial.begin(115200);
    Serial2.begin(UART_BAUD, SERIAL_8N1, 16, 17);

    // I2C + PCA9685
    Wire.begin(21, 22);   // SDA=21, SCL=22
    servo_init();

    // Motors
    motor_init();
    g_last_cmd = millis();

    Serial.println("RBC-bn ready. UART on Serial2 (RX=16, TX=17).");
}

void loop() {
    // --- Đọc UART từ Pi 5 (Serial2) ---
    while (Serial2.available() > 0) {
        uint8_t b = Serial2.read();
        uart_parse_byte(b);
    }

    // --- Safety timeout: auto-STOP nếu không nhận lệnh ---
    if (millis() - g_last_cmd > CMD_TIMEOUT_MS) {
        g_cmd     = CMD_STOP;
        g_speed_l = 0;
        g_speed_r = 0;
    }

    // --- Thực thi lệnh ---
    execute_cmd(g_cmd, g_speed_l, g_speed_r);

    delay(10);  // ~100 Hz loop
}
