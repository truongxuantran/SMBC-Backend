from flask import Blueprint, current_app, g, request
from injector import inject

from app.services import UserService
from app.views.api.schemas import LoginInputSchema

from ..responses import Error, Token

app = Blueprint('api.auth', __name__)


@app.route("/signin", methods=["POST"])
@inject
def signin(user_service: UserService):
    request_data = request.get_json()
    LoginInputSchema().load(request_data)
    input_data = {
        'email': request_data['email'],
        'password': request_data['password']
    }

    user = user_service.login(**input_data)
    return Token(user).response()


@app.route("/signup", methods=["POST"])
@inject
def signup(user_service: UserService):
    request_data = request.get_json()
    LoginInputSchema().load(request_data)
    input_data = {
        'email': request_data['email'],
        'password': request_data['password']
    }

    user = user_service.create_user(input_data)
    return Token(user).response()


@app.route('/forgot-password', methods=["POST"])
@request_log
@inject
def forgot_password(user_service: UserService, mail_service: MailService,
                    email_token_service: EmailTokenService):

    request_data = request.get_json()
    ForgotPasswordSchema().load(request_data)

    email = request_data.get('email')
    user = user_service.get_user_by_email(email)
    if user is None:
        # response success if user not found
        return Status("A reset password email has sent").response()

    reset_password_token = email_token_service.create_token(email)
    reset_password_url = f"{Config.APP_URL}/#/reset-password?token={reset_password_token}"
    html = render_template('mails/forgot_password.html',
                           url=reset_password_url)
    mail_service.send_mail([email], '[Kaizen] Password Reset', '', html)

    return Status("A reset password email has sent").response()


@app.route('/reset-password', methods=["POST"])
@request_log
@inject
def reset_password(user_service: UserService,
                   email_token_service: EmailTokenService):
    request_data = request.get_json()
    ResetPasswordSchema().load(request_data)

    token = request_data.get('token')
    email_token_service.validate(token)

    email_token = email_token_service.get_email_token_by_token(token)
    if email_token is None:
        raise ParameterError('Token invalid')

    user = user_service.get_user_by_email(email_token.email)
    if user is None:
        raise NotFoundError('User not found')

    updated = user_service.update_user(user, {
        'password': request_data.get('password'),
    })

    if updated is not None:
        email_token_service.delete(email_token)

    return Status("Reset password successfully").response()


@app.route('/verify-token', methods=["POST"])
@inject
def verify_password_token(email_token_service: EmailTokenService):
    request_data = request.get_json()
    CheckPasswordTokenSchema().load(request_data)

    token = request_data.get('token')
    email_token = email_token_service.get_email_token_by_token(token)
    if email_token is None:
        raise APIResponseError('Token invalid')
    try:
        jwt.decode(token, Config.SECRET_KEY, algorithms='HS256')
    except AttributeError:
        raise APIResponseError('Token does not exist.')
    except jwt.DecodeError:
        raise APIResponseError('Token is invalid.')
    except jwt.ExpiredSignatureError as e:
        raise APIResponseError('Token is expired.')

    return Status("Token valid").response()
