from flask import render_template, redirect, url_for, flash, request
from . import auth
from .forms import LoginForm, RegisterationForm, changePasswordForm, forgetPasswordRequestForm, resetPasswordForm
from ..models import User
from flask_login import login_user, logout_user, login_required, current_user
from .. import db
from ..email import send_email

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
            and request.endpoint \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route("/login",  methods=["GET","POST"])
def login():
    loginError = None
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get("next") or url_for("main.index"))
        loginError="Invalid emial or password"
    return render_template("auth/login.html", form=form,loginError=loginError)

@auth.route("/logout", methods=["GET","POST"])
@login_required
def logout():
    logout_user()
    flash("You has been logged out.")
    return redirect(url_for("auth.login"))

@auth.route("/register",  methods=["GET","POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegisterationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, password=form.password.data, username=form.username.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, "Confirm Your Account", "auth/email/confirm",user=user,token=token)
        flash("A confirmation email has been sent to your email")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)

@auth.route("/confirm/<token>",  methods=["GET","POST"])
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for("main.index"))
    if current_user.confirm(token):
        flash("You have confirmed your account.")
    else:
        flash("The confirmation link is invalid or has expired")
    return redirect(url_for("main.index"))

@auth.route("/confirm",  methods=["GET","POST"])
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, "Confirm Your Account", "auth/email/confirm",user=current_user,token=token)
    flash("A new confirmation email has been sent to your email")
    return redirect(url_for("main.index"))


@auth.route("/changePassword",  methods=["GET","POST"])
@login_required
def change_password():
    form = changePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.password.data
        db.session.add(current_user)
        flash("Change password successfully")
        return redirect(url_for("main.index"))
    return render_template("auth/changePassword.html", form=form)

@auth.route("/forgetPasswordRequest",  methods=["GET","POST"])
def forget_password_request():
    form = forgetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            token = user.generate_resetPassword_token()
            send_email(user.email, "Reset Your password", "auth/email/resetPassword",user=user,token=token)
        return render_template('auth/forgetPassswordNotificationMessage.html',email=form.email.data)
    return render_template("auth/forgetPasswordRequest.html", form=form)

@auth.route("/resetPassword/<token>",  methods=["GET","POST"])
def reset_password(token):
    form = resetPasswordForm()
    if form.validate_on_submit():
        user = User.confirm_token_user(token)
        if user:
            user.password = form.password.data
            db.session.add(user)
            login_user(user)
            flash("Reset password Successfully!")
        else:
            flash("Reset password failed!")
            redirect(url_for("auth.main"))
        return redirect(url_for('auth.login'))
    return render_template("auth/resetPassword.html", form=form)

'''
@auth.route("/resetPassword",  methods=["GET","POST"])
def reset_password():
    form = resetPasswordForm()
    if form.validate_on_submit():
        token = request.args.get('token',None)
        user = User.confirm_token_user(token)
        if user:
            user.password = form.password.data
            db.session.add(user)
            login_user(user)
        else:
            flash("Reset password failed!")
        return redirect(url_for("main.index"))
    return render_template("auth/resetPassword.html", form=form)
'''
