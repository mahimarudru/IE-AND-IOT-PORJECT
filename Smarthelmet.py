from gpiozero import Button, LED
from signal import pause
import time
import smbus2
from twilio.rest import Client
import sys

# --- GPIO Pins ---
helmet_touch = Button(17, pull_up=True)         # TTP223 Touch Sensor (Active LOW)
alcohol_sensor_pin = Button(7, pull_up=True)    # MQ3 D0 (Active LOW)
buzzer = LED(21)                                # Buzzer control via GPIO 21

# --- Twilio Setup ---
account_sid = 'your_account_sid_here'  # Replace with your Twilio Account SID
auth_token = 'your_auth_token_here'  # Replace with your Twilio Auth Token
twilio_number = '+1234567890'  # Replace with your Twilio phone number
relative_number = '+1234567890'  # Replace with your Twilio phone number

client = Client(account_sid, auth_token)

# --- MPU6050 Setup ---
MPU_ADDR = 0x68
bus = smbus2.SMBus(1)

def init_mpu():
    try:
        bus.write_byte_data(MPU_ADDR, 0x6B, 0)  # Wake up sensor
        print("✅ MPU Initialized.")
    except:
        print("❌ MPU Initialization Failed.")

def read_word_2c(addr):
    high = bus.read_byte_data(MPU_ADDR, addr)
    low = bus.read_byte_data(MPU_ADDR, addr + 1)
    val = (high << 8) + low
    return val - 65536 if val > 32767 else val

def read_accel():
    acc_x = read_word_2c(0x3B) / 16384.0
    acc_y = read_word_2c(0x3D) / 16384.0
    acc_z = read_word_2c(0x3F) / 16384.0
    return acc_x, acc_y, acc_z

def detect_fall():
    acc_x, acc_y, acc_z = read_accel()
    total_acc = (acc_x*2 + acc_y2 + acc_z2)*0.5
    print(f"📈 Acceleration: {total_acc:.2f}g")
    return total_acc > 2.5  # Fall threshold

def send_sms(message):
    try:
        client.messages.create(body=message, from_=twilio_number, to=relative_number)
        print("📩 SMS sent:", message)
    except Exception as e:
        print("❌ SMS send failed:", e)

# --- Main ---
init_mpu()
fall_detected = False

print("🟢 Smart Helmet System Started...\n")

try:
    while True:
        helmet_on = not helmet_touch.is_pressed
        alcohol_detected = alcohol_sensor_pin.is_pressed

        if helmet_on:
            print("🪖 Helmet is WORN")

            if not alcohol_detected:
                print("🍃 No alcohol detected.")

                if detect_fall():
                    if not fall_detected:
                        print("🚨 Fall detected! Sending SMS.")
                        send_sms("🚨 Accident detected! Rider may need help.")
                        buzzer.on()
                        time.sleep(5)
                        buzzer.off()
                        print("🔚 Exiting system after accident.")
                        sys.exit()
                else:
                    fall_detected = False
                    buzzer.off()
            else:
                print("⚠ Alcohol detected! Sending SMS.")
                send_sms("⚠ Alcohol detected in rider's breath. Ride blocked.")
                buzzer.on()
                time.sleep(5)
                buzzer.off()

        else:
            print("🚫 Helmet NOT worn. Ignition locked.")
            buzzer.on()
            time.sleep(2)
            buzzer.off()

        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 System manually stopped.")
    buzzer.off()