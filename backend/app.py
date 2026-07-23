from flask import Flask, render_template, request
import psycopg2
from config import Config

from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "travelgo_secret_key"

def get_db_connection():
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )
    return conn


from datetime import datetime, date


@app.route("/", methods=["GET", "POST"])
def home():

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        buses = []
        journey_date = None

        if request.method == "POST":

            source = request.form["source"].strip()
            destination = request.form["destination"].strip()
            journey_date = request.form["journey_date"]

            # Validate journey date
            selected_date = datetime.strptime(
                journey_date, "%Y-%m-%d"
            ).date()

            if selected_date < date.today():

                cur.close()
                conn.close()

                return render_template(
                    "index.html",
                    buses=[],
                    journey_date=journey_date,
                    error="❌ Please select today or a future date."
                )

            # Search buses
            cur.execute("""
                SELECT
                    bus_id,
                    bus_name,
                    source,
                    destination,
                    departure_time,
                    arrival_time,
                    price,
                    available_seats,
                    bus_type,
                    rating,
                    duration
                FROM buses
                WHERE source=%s
                AND destination=%s
                ORDER BY departure_time;
            """, (source, destination))

            buses = cur.fetchall()

        else:

            cur.execute("""
                SELECT
                    bus_id,
                    bus_name,
                    source,
                    destination,
                    departure_time,
                    arrival_time,
                    price,
                    available_seats,
                    bus_type,
                    rating,
                    duration
                FROM buses
                ORDER BY departure_time;
            """)

            buses = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            "index.html",
            buses=buses,
            journey_date=journey_date
        )

    except Exception as e:
        return f"<h2>❌ Error</h2><p>{e}</p>"

@app.route("/bus/<int:bus_id>")
def bus_details(bus_id):

    journey_date = request.args.get("journey_date")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                bus_id,
                bus_name,
                source,
                destination,
                departure_time,
                arrival_time,
                price,
                available_seats,
                bus_type,
                rating,
                duration
            FROM buses
            WHERE bus_id = %s;
        """, (bus_id,))

        bus = cur.fetchone()

        cur.close()
        conn.close()

        if bus is None:
            return "<h2>Bus not found!</h2>", 404

        return render_template(
            "bus_details.html",
            bus=bus,
            journey_date=journey_date
        )

    except Exception as e:
        return f"<h2>❌ Error</h2><p>{e}</p>"
    
@app.route("/bus/<int:bus_id>/seats")
def select_seat(bus_id):

    journey_date = request.args.get("journey_date")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get bus details
        cur.execute("""
            SELECT
                bus_id,
                bus_name,
                source,
                destination,
                departure_time,
                arrival_time,
                price,
                available_seats,
                bus_type,
                rating,
                duration
            FROM buses
            WHERE bus_id = %s;
        """, (bus_id,))

        bus = cur.fetchone()

        if bus is None:
            cur.close()
            conn.close()
            return "<h2>Bus not found!</h2>", 404

        # Get seat details
        cur.execute("""
            SELECT
                seat_id,
                seat_number,
                is_booked
            FROM seats
            WHERE bus_id = %s
            ORDER BY seat_number;
        """, (bus_id,))

        seats = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            "seat_selection.html",
            bus=bus,
            seats=seats,
            journey_date=journey_date
        )

    except Exception as e:
        return f"<h2>❌ Error</h2><p>{e}</p>"
@app.route("/passenger-details")
def passenger_details():

    seats = request.args.get("seats")
    bus_id = request.args.get("bus")
    journey_date = request.args.get("journey_date")

    if not seats or not bus_id:
        return "<h2>Invalid Request</h2>", 400

    seat_list = seats.split(",")    

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                bus_id,
                bus_name,
                source,
                destination,
                departure_time,
                arrival_time,
                price,
                available_seats,
                bus_type,
                rating,
                duration
            FROM buses
            WHERE bus_id = %s;
        """, (bus_id,))

        bus = cur.fetchone()

        cur.close()
        conn.close()

        if bus is None:
            return "<h2>Bus not found!</h2>", 404

        return render_template(
            "passenger_details.html",
            bus=bus,
            seats=seat_list,
            bus_id=bus_id,
            journey_date=journey_date
        )   

    except Exception as e:
        return f"<h2>❌ Error</h2><p>{e}</p>"

    
@app.route("/payment", methods=["POST"])

def payment():

    bus_id = request.form.get("bus_id")

    seats = request.form.getlist("seat[]")
    names = request.form.getlist("name[]")
    ages = request.form.getlist("age[]")
    genders = request.form.getlist("gender[]")

    mobile = request.form.get("mobile")
    email = request.form.get("email")
    journey_date = request.form.get("journey_date")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                bus_id,
                bus_name,
                source,
                destination,
                departure_time,
                arrival_time,
                price,
                available_seats,
                bus_type,
                rating,
                duration
            FROM buses
            WHERE bus_id = %s;
        """, (bus_id,))

        bus = cur.fetchone()

        cur.close()
        conn.close()

        if bus is None:
            return "<h2>Bus not found!</h2>", 404

        
        ticket_fare = bus[6] * len(seats)
        total_amount = ticket_fare + 30

        return render_template(
            "payment.html",
            bus=bus,
            bus_id=bus_id,
            seats=seats,
            names=names,
            ages=ages,
            genders=genders,
            mobile=mobile,
            email=email,
            journey_date=journey_date,
            total_amount=total_amount
        )

    except Exception as e:
        return f"<h2>❌ Error</h2><p>{e}</p>"
@app.route("/confirm-booking", methods=["POST"])
def confirm_booking():

    # Check user login
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    bus_id = request.form.get("bus_id")
    mobile = request.form.get("mobile")
    email = request.form.get("email")
    payment_method = request.form.get("payment_method")

    seats = request.form.getlist("seat[]")
    names = request.form.getlist("name[]")
    ages = request.form.getlist("age[]")
    genders = request.form.getlist("gender[]")

    print("=" * 40)
    print("Logged in user:", user_id)
    print("bus_id:", bus_id)
    print("seats:", seats)
    print("Form Data:", request.form)
    print("=" * 40)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get ticket price
        cur.execute(
            "SELECT price FROM buses WHERE bus_id = %s;",
            (bus_id,)
        )

        result = cur.fetchone()

        if result is None:
            return "<h2>Bus not found!</h2>", 404

        price = result[0]
        total_amount = (price * len(seats)) + 30

        # Create booking
        cur.execute("""
            INSERT INTO bookings
            (
                user_id,
                bus_id,
                mobile,
                email,
                payment_method,
                total_amount
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING booking_id;
        """, (
            user_id,
            bus_id,
            mobile,
            email,
            payment_method,
            total_amount
        ))

        booking_id = cur.fetchone()[0]

        # Save passenger details
        for i in range(len(seats)):
            cur.execute("""
                INSERT INTO booking_passengers
                (
                    booking_id,
                    passenger_name,
                    age,
                    gender,
                    seat_number
                )
                VALUES (%s, %s, %s, %s, %s);
            """, (
                booking_id,
                names[i],
                ages[i],
                genders[i],
                seats[i]
            ))

        # Mark seats as booked
        for seat in seats:
            cur.execute("""
                UPDATE seats
                SET is_booked = TRUE
                WHERE bus_id = %s
                AND seat_number = %s;
            """, (
                bus_id,
                seat
            ))

        # Update available seats
        cur.execute("""
            UPDATE buses
            SET available_seats = available_seats - %s
            WHERE bus_id = %s;
        """, (
            len(seats),
            bus_id
        ))

        conn.commit()

        cur.close()
        conn.close()

        return render_template(
            "booking_confirmation.html",
            booking_id=booking_id,
            bus_id=bus_id,
            seats=seats,
            total_amount=total_amount,
            payment_method=payment_method
        )

    except Exception as e:

        if 'conn' in locals():
            conn.rollback()

        if 'cur' in locals():
            cur.close()

        if 'conn' in locals():
            conn.close()

        return f"<h2>❌ Error</h2><p>{e}</p>"
@app.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/login")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                b.booking_id,
                bs.bus_name,
                bs.source,
                bs.destination,
                bp.passenger_name,
                bp.seat_number,
                b.total_amount,
                b.payment_method,
                b.booking_time,
                b.status
            FROM bookings b
            JOIN buses bs
                ON b.bus_id = bs.bus_id
            JOIN booking_passengers bp
                ON b.booking_id = bp.booking_id
            WHERE b.user_id = %s
            ORDER BY b.booking_time DESC;
        """, (session["user_id"],))

        bookings = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            "my_bookings.html",
            bookings=bookings
        )

    except Exception as e:
        return f"<h2>Error</h2><p>{e}</p>"
    
@app.route("/offers")
def offers():
    return render_template("offers.html")

@app.route("/help")
def help():
    return render_template("help.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO contact_messages
                (
                    name,
                    email,
                    message
                )
                VALUES (%s, %s, %s)
            """, (name, email, message))

            conn.commit()

            cur.close()
            conn.close()

            return render_template(
                "contact.html",
                success="✅ Thank you! Your message has been sent successfully."
            )

        except Exception as e:

            if 'conn' in locals():
                conn.rollback()
                conn.close()

            return render_template(
                "contact.html",
                error=f"Error: {e}"
            )

    return render_template("contact.html")


from flask import request, redirect, render_template
from werkzeug.security import generate_password_hash,check_password_hash
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["mobile"].strip()
        password = generate_password_hash(request.form["password"])

        conn = None

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Check if email already exists
            cur.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (email,)
            )

            existing_user = cur.fetchone()

            if existing_user:
                cur.close()
                conn.close()

                return render_template(
                    "register.html",
                    error="Email is already registered. Please use another email."
                )

            # Insert new user
            cur.execute("""
                INSERT INTO users (full_name, email, phone, password)
                VALUES (%s, %s, %s, %s)
            """, (full_name, email, phone, password))

            conn.commit()

            cur.close()
            conn.close()

            return redirect("/login")

        except Exception as e:

            if conn:
                conn.rollback()
                conn.close()

            return render_template(
                "register.html",
                error=f"Registration failed: {str(e)}"
            )

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id, full_name, email, password
            FROM users
            WHERE LOWER(email) = %s
        """, (email,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:

            stored_password = user[3]

            if check_password_hash(stored_password, password):

                session["user_id"] = user[0]
                session["user_name"] = user[1]
                session["user_email"] = user[2]

                return redirect("/")

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

@app.route("/cancel-booking/<int:booking_id>")
def cancel_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE bookings
        SET status = 'Cancelled'
        WHERE booking_id = %s
    """, (booking_id,))

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/my-bookings")


if __name__ == "__main__":
    app.run(debug=True)