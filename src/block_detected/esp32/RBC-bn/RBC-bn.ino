/**
 * RBC-bn — Robot Block Chaser (4-wheel mecanum)
 * ESP32 firmware: nhận lệnh UART từ Raspberry Pi 5 → điều khiển 4 bánh mecanum
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
 * Mecanum wheel mapping (front view, robot top):
 *    FL —— FR        FL: motor 1 (front-left)
 *    |      |        FR: motor 2 (front-right)
 *    |      |        RL: motor 3 (rear-left)
 *    RL —— RR        RR: motor 4 (rear-right)
 *
 * Mecanum kinematics:
 *   V_fl = V_y + V_x + ω    V_fr = V_y - V_x - ω
 *   V_rl = V_y - V_x + ω    V_rr = V_y + V_x - ω
 *
 * Pin mapping (điều chỉnh theo phần cứng thực tế):
 *   Motor FL: ENA=gpio, IN1=gpio, IN2=gpio
 *   Motor FR: ENB=gpio, IN3=gpio, IN4=gpio
 *   Motor RL: ENC=gpio, IN5=gpio, IN6=gpio
 *   Motor RR: END=gpio, IN7=gpio, IN8=gpio
 */

#include <Arduino.h>

// ============================================================
// Pin definitions — PWM-capable GPIOs cho ESP32
// ============================================================

// Front-Left (FL)
#define FL_EN   12   // PWM
#define FL_IN1  13
#define FL_IN2  14

// Front-Right (FR)
#define FR_EN   25   // PWM
#define FR_IN1  26
#define FR_IN2  27

// Rear-Left (RL)
#define RL_EN   32   // PWM
#define RL_IN1  33
#define RL_IN2  15   // OK on ESP32 (not strapping)

// Rear-Right (RR)
#define RR_EN   4    // PWM (tránh GPIO 0,2,5 nếu dùng strapping)
#define RR_IN1  16
#define RR_IN2  17

// ============================================================
// PWM settings
// ============================================================
#define PWM_FREQ       5000    // 5 kHz
#define PWM_RESOLUTION 8       // 0-255
#define PWM_CH_FL      0
#define PWM_CH_FR      1
#define PWM_CH_RL      2
#define PWM_CH_RR      3

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

#define CMD_TIMEOUT_MS   500   // Auto-stop nếu không nhận lệnh sau timeout

// ============================================================
// State
// ============================================================
static uint8_t  g_cmd      = CMD_STOP;
static uint8_t  g_speed_l  = 0;
static uint8_t  g_speed_r  = 0;
static uint32_t g_last_cmd = 0;

// ============================================================
// Motor helpers
// ============================================================

void motor_init() {
    // Setup PWM channels
    ledcSetup(PWM_CH_FL, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(PWM_CH_FR, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(PWM_CH_RL, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(PWM_CH_RR, PWM_FREQ, PWM_RESOLUTION);

    // Attach pins to PWM channels
    ledcAttachPin(FL_EN, PWM_CH_FL);
    ledcAttachPin(FR_EN, PWM_CH_FR);
    ledcAttachPin(RL_EN, PWM_CH_RL);
    ledcAttachPin(RR_EN, PWM_CH_RR);

    // Direction pins as outputs
    pinMode(FL_IN1, OUTPUT); pinMode(FL_IN2, OUTPUT);
    pinMode(FR_IN1, OUTPUT); pinMode(FR_IN2, OUTPUT);
    pinMode(RL_IN1, OUTPUT); pinMode(RL_IN2, OUTPUT);
    pinMode(RR_IN1, OUTPUT); pinMode(RR_IN2, OUTPUT);

    motor_stop_all();
}

void motor_set(uint8_t en_pin, int pwm_ch, int in1, int in2, int speed) {
    // speed: dương = forward/left, âm = backward/right
    if (speed > 0) {
        digitalWrite(in1, HIGH);
        digitalWrite(in2, LOW);
    } else if (speed < 0) {
        digitalWrite(in1, LOW);
        digitalWrite(in2, HIGH);
        speed = -speed;
    } else {
        digitalWrite(in1, LOW);
        digitalWrite(in2, LOW);
    }
    ledcWrite(pwm_ch, constrain(speed, 0, 255));
}

void motor_stop_all() {
    ledcWrite(PWM_CH_FL, 0);
    ledcWrite(PWM_CH_FR, 0);
    ledcWrite(PWM_CH_RL, 0);
    ledcWrite(PWM_CH_RR, 0);
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
 *   Vx = strafe (dương = right), Vy = forward (dương = forward), ω = rotation (dương = CCW)
 *
 *   Mỗi bánh = Vy + Vx_sign * Vx + ω_sign * ω
 */
void mecanum_drive(int vx, int vy, int omega) {
    int fl = vy + vx + omega;   // front-left
    int fr = vy - vx - omega;   // front-right
    int rl = vy - vx + omega;   // rear-left
    int rr = vy + vx - omega;   // rear-right

    motor_set(FL_EN, PWM_CH_FL, FL_IN1, FL_IN2, fl);
    motor_set(FR_EN, PWM_CH_FR, FR_IN1, FR_IN2, fr);
    motor_set(RL_EN, PWM_CH_RL, RL_IN1, RL_IN2, rl);
    motor_set(RR_EN, PWM_CH_RR, RR_IN1, RR_IN2, rr);
}

// ============================================================
// Command handler
// ============================================================

void execute_cmd(uint8_t cmd, uint8_t speed_l, uint8_t speed_r) {
    int s = (int)constrain(speed_l, 0, 255);

    switch (cmd) {
        case CMD_FORWARD:
            mecanum_drive(0, s, 0);          // Vy = +speed
            break;
        case CMD_BACKWARD:
            mecanum_drive(0, -s, 0);         // Vy = -speed
            break;
        case CMD_LEFT:
            mecanum_drive(-s, 0, 0);         // Vx = -speed (strafe left)
            break;
        case CMD_RIGHT:
            mecanum_drive(s, 0, 0);          // Vx = +speed (strafe right)
            break;
        case CMD_STOP:
            mecanum_drive(0, 0, 0);
            break;
        case CMD_ROTATE_LEFT:
            mecanum_drive(0, 0, s);          // ω = +speed (CCW)
            break;
        case CMD_ROTATE_RIGHT:
            mecanum_drive(0, 0, -s);         // ω = -speed (CW)
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
                // Checksum mismatch → discard, wait for next frame
                parse_state = WAIT_START;
            }
            break;
        }
        case WAIT_END:
            if (b == FRAME_END) {
                // Valid frame received
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
// Setup / Loop
// ============================================================

void setup() {
    Serial.begin(UART_BAUD);
    // RX2/TX2 có thể dùng nếu cần UART riêng cho robot:
    // Serial2.begin(UART_BAUD, SERIAL_8N1, 16, 17);

    motor_init();
    g_last_cmd = millis();

    // LED onboard báo hiệu sẵn sàng
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);
}

void loop() {
    // --- Đọc UART ---
    while (Serial.available() > 0) {
        uint8_t b = Serial.read();
        uart_parse_byte(b);
    }

    // --- Safety timeout: auto-stop nếu không nhận lệnh ---
    if (millis() - g_last_cmd > CMD_TIMEOUT_MS) {
        g_cmd     = CMD_STOP;
        g_speed_l = 0;
        g_speed_r = 0;
    }

    // --- Thực thi lệnh ---
    execute_cmd(g_cmd, g_speed_l, g_speed_r);

    // --- Nhịp tim LED ---
    static uint32_t last_blink = 0;
    if (millis() - last_blink > 500) {
        last_blink = millis();
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    }

    delay(10);  // ~100 Hz loop
}
