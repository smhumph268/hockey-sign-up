from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import CustomUser


class CustomUserModelTests(TestCase):

    def setUp(self):
        self.email = 'test@email.com'
        self.password = 'testPassword1'
        self.username = 'testUser1'
        self.first_name = 'Testy'
        self.last_name = 'Usersmith'
        self.superEmail = 'admin@email.com'
        self.superUsername = 'admin'
        self.superPassword = 'adminPass1234'

    def test_user_creation(self):
        """
        Test that a user was created with the correct data
        """
        MyUserModel = get_user_model()
        user = MyUserModel.objects.create_user(email=self.email,
                                               password=self.password,
                                               username=self.username,
                                               first_name=self.first_name,
                                               last_name=self.last_name)
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.email, self.email)
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_active)

    def test_create_superuser(self):
        """
        Test that a superuser was created with the correct data
        """
        MyUserModel = get_user_model()
        superuser = MyUserModel.objects.create_superuser(email=self.superEmail,
                                                         password=self.superPassword,
                                                         username=self.superUsername)
        self.assertIsInstance(superuser, CustomUser)
        self.assertEqual(superuser.email, self.superEmail)
        self.assertTrue(superuser.check_password(self.superPassword))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)


class HomePageViewTests(TestCase):

    def setUp(self):
        self.email = 'test@email.com'
        self.password = 'testPassword1'
        self.username = 'testUser1'
        self.loginURL = reverse('users:login')
        self.logoutURL = reverse('users:logout')
        self.indexURL = reverse('dropins:index')
        self.registerURL = reverse('users:register')
        MyUserModel = get_user_model()
        user = MyUserModel.objects.create_user(email=self.email,
                                        password=self.password,
                                        username=self.username)
        # Users will be set to inactive upon creation because of the receiver defined in models.py
        user.is_active = True
        user.save()

    def test_see_login_and_register_when_logged_in_dont_see_logout(self):
        """
        Test user sees login and register URL if they aren't already logged in
        """
        response = self.client.get(self.indexURL, follow=True)
        # Shouldn't see logout URL
        self.assertTrue(response.content.decode(response.charset).__contains__(self.loginURL))
        self.assertTrue(response.content.decode(response.charset).__contains__(self.registerURL))
        self.assertFalse(response.content.decode(response.charset).__contains__(self.logoutURL))

    def test_see_logout_when_not_logged_in_dont_see_login_or_register(self):
        """
        Test user sees logout URL if they are already logged in
        """
        # send login data, go to home page
        self.client.post(self.loginURL, {'username': self.email, 'password': self.password}, follow=True)
        response = self.client.get(self.indexURL, follow=True)
        # Shouldn't see login and register URLs
        self.assertFalse(response.content.decode(response.charset).__contains__(self.loginURL))
        self.assertFalse(response.content.decode(response.charset).__contains__(self.registerURL))
        self.assertTrue(response.content.decode(response.charset).__contains__(self.logoutURL))


class RegisterViewTests(TestCase):
    def setUp(self):
        self.email = 'test@email.com'
        self.username = 'testUser1'
        self.firstname = 'Testy'
        self.lastname = 'McTest'
        self.skill_level = 'b'
        self.preferred_position = 'goalie'
        self.password1 = 'testPassword1'
        self.password2 = 'testPassword1'
        self.registerURL = reverse('users:register')

    def test_register_success(self):
        """
        Test that user can register successfully
        """
        # send register data
        response = self.client.post(self.registerURL,
                                    {
                                        'email': self.email,
                                        'username': self.username,
                                        'first_name': self.firstname,
                                        'last_name': self.lastname,
                                        'skill_level': self.skill_level,
                                        'preferred_position': self.preferred_position,
                                        'password1': self.password1,
                                        'password2': self.password2
                                    },
                                    follow=True)
        # should see register success message
        self.assertTrue(response.content.decode(response.charset).__contains__(
            'Your account has been created and is pending review. You can login once approved.'))

    def test_register_fail_from_email_input(self):
        """
        Test that registration fails when given email is bad
        """
        # send register data
        response = self.client.post(self.registerURL,
                                    {
                                        'email': 'address@missingdotcom',
                                        'username': self.username,
                                        'first_name': self.firstname,
                                        'last_name': self.lastname,
                                        'skill_level': self.skill_level,
                                        'preferred_position': self.preferred_position,
                                        'password1': self.password1,
                                        'password2': self.password2
                                    },
                                    follow=True)
        # should see register success message
        self.assertTrue(response.content.decode(response.charset).__contains__(
            'Enter a valid email address'))

    def test_register_fail_from_mismatch_password_input(self):
        """
        Test that registration fails when given mismatched passwords
        """
        # send register data
        response = self.client.post(self.registerURL,
                                    {
                                        'email': self.email,
                                        'username': self.username,
                                        'first_name': self.firstname,
                                        'last_name': self.lastname,
                                        'skill_level': self.skill_level,
                                        'preferred_position': self.preferred_position,
                                        'password1': self.password1,
                                        'password2': 'mismatch'
                                    },
                                    follow=True)
        # should see register success message
        self.assertTrue(response.content.decode(response.charset).__contains__(
            'The two password fields didn’t match'))

    def test_register_fail_from_bad_select_option_input(self):
        """
        Test that registration fails when given mismatched passwords
        """
        # send register data
        response = self.client.post(self.registerURL,
                                    {
                                        'email': self.email,
                                        'username': self.username,
                                        'first_name': self.firstname,
                                        'last_name': self.lastname,
                                        'skill_level': 'f',
                                        'preferred_position': self.preferred_position,
                                        'password1': self.password1,
                                        'password2': self.password1
                                    },
                                    follow=True)
        # should see register success message
        self.assertTrue(response.content.decode(response.charset).__contains__(
            'Select a valid choice. f is not one of the available choices.'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            'Please resolve registration errors'))


class LoginViewTests(TestCase):
    def setUp(self):
        self.email = 'test@email.com'
        self.password = 'testPassword1'
        self.username = 'testUser1'
        self.skill_level = 'b'
        self.preferred_position = 'goalie'
        self.loginURL = reverse('users:login')
        self.registerURL = reverse('users:register')
        user = get_user_model().objects.create_user(email=self.email,
                                                    password=self.password,
                                                    username=self.username,
                                                    is_active=True)
        # Users will be set to inactive upon creation because of the receiver defined in models.py
        user.is_active = True
        user.save()

    def test_login_success_with_username(self):
        """
        Test that user can log in with username
        """
        # send login data
        response = self.client.post(self.loginURL, {'username': self.username, 'password': self.password}, follow=True)
        # should be logged in now
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_success_with_email(self):
        """
        Test that user can log in with email
        """
        # send login data
        response = self.client.post(self.loginURL, {'username': self.email, 'password': self.password}, follow=True)
        # should be logged in now
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_fail_account_inactive_after_registration(self):
        """
        Test that user login will fail if they register and aren't activated yet
        """
        # send register data
        email = 'test2@email.com'
        password = 'testPassword1'
        username = 'testUser2'
        self.client.post(self.registerURL,
            {
                'email': email,
                'username': username,
                'first_name': 'John',
                'last_name': 'Doe',
                'skill_level': self.skill_level,
                'preferred_position': self.preferred_position,
                'password1': password,
                'password2': password
            },
            follow=True)
        # send login data
        response = self.client.post(self.loginURL, {'username': username, 'password': password}, follow=True)
        # should not be logged in now
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertTrue(response.content.decode(response.charset).__contains__('This account is inactive.'))

    def test_login_fail_bad_username(self):
        """
        Test that user login will fail if given a bad username
        """
        # send login data
        response = self.client.post(self.loginURL, {'username': 'bad@mail.com', 'password': self.password}, follow=True)
        # should not be logged in now
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertTrue(response.content.decode(response.charset).__contains__(
                            'Please enter a correct email and password. Note that both fields may be case-sensitive'))

    def test_login_fail_bad_password(self):
        """
        Test that user login will fail if given a bad password
        """
        # send login data
        response = self.client.post(self.loginURL, {'username': self.email, 'password': 'bad'}, follow=True)
        # should not be logged in now
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertTrue(response.content.decode(response.charset).__contains__(
                            'Please enter a correct email and password. Note that both fields may be case-sensitive'))

    def test_already_logged_in(self):
        """
        Test that user's who are already logged in won't have option to login
        """
        # send login data
        self.client.post(self.loginURL, {'username': self.email, 'password': self.password}, follow=True)
        # User who is already logged in shouldn't have option to reach login page, but if they do, let them know
        response = self.client.get(reverse('users:login'), follow=True)
        self.assertTrue(response.content.decode(response.charset).__contains__(
                            'Already logged in as '+self.username))


class LogoutViewTests(TestCase):
    def setUp(self):
        self.email = 'test@email.com'
        self.password = 'testPassword1'
        self.username = 'testUser1'
        self.loginURL = reverse('users:login')
        self.logoutURL = reverse('users:logout')
        MyUserModel = get_user_model()
        user = MyUserModel.objects.create_user(email=self.email,
                                        password=self.password,
                                        username=self.username)
        # Users will be set to inactive upon creation because of the receiver defined in models.py
        user.is_active = True
        user.save()

    def test_logout_when_already_logged_in(self):
        """
        Test that user's who are already logged in can log out successfully
        """
        # send login data
        response = self.client.post(self.loginURL, {'username': self.email, 'password': self.password}, follow=True)
        # assert authenticated, then logout and assert unauthenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        response = self.client.get(self.logoutURL, follow=True)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_when_not_logged_in(self):
        """
        Test that user's who aren't already logged in stay not logged in
        """
        # logout and assert unauthenticated
        response = self.client.get(self.logoutURL, follow=True)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.email = 'test@email.com'
        self.password = 'testPassword1'
        self.username = 'testUser1'
        self.loginURL = reverse('users:login')
        MyUserModel = get_user_model()
        self.user = MyUserModel.objects.create_user(email=self.email,
                                                    password=self.password,
                                                    username=self.username)
        # Users will be set to inactive upon creation because of the receiver defined in models.py
        self.user.is_active = True
        self.user.save()

        # create second user for testing that users can't view each other's profiles
        self.user2 = MyUserModel.objects.create_user(email='test2@email.com',
                                                     password='testPassword2',
                                                     username='testUser2')

    def test_changing_from_default_profile_values(self):
        """
        Test that user has default skill_level and preferred_position values and then updates them to different values
        """
        # check that user has default values
        self.assertTrue(self.user.skill_level == 'd')
        self.assertTrue(self.user.preferred_position == 'forward')
        # login as the user
        self.client.post(self.loginURL, {'username': self.username, 'password': self.password}, follow=True)
        # send updated profile data
        response = self.client.post(reverse('users:profile', kwargs={'user_id': self.user.id}),
                                    {
                                        'skill_level': 'c',
                                        'preferred_position': 'defense'
                                    },
                                    follow=True)
        # should see updated values and should see update success message
        self.user.refresh_from_db()  # need to refresh from the database after using the form
        self.assertTrue(self.user.skill_level == 'c')
        self.assertTrue(self.user.preferred_position == 'defense')
        self.assertTrue(response.content.decode(response.charset).__contains__('Your details have been updated.'))

    def test_give_bad_option_to_select_field(self):
        """
        Test that logged-in user will see error message when trying to provide bad values to the select field
        """
        # login as the user
        self.client.post(self.loginURL, {'username': self.username, 'password': self.password}, follow=True)
        # send updated profile data
        response = self.client.post(reverse('users:profile', kwargs={'user_id': self.user.id}),
                                    {
                                        'skill_level': 'f',
                                        'preferred_position': 'defense'
                                    },
                                    follow=True)
        # should see original (default) values and should see error message
        self.user.refresh_from_db()  # refresh from the database after using the form
        self.assertTrue(self.user.skill_level == 'd')
        self.assertTrue(self.user.preferred_position == 'forward')
        self.assertTrue(response.content.decode(response.charset).__contains__(
            'Select a valid choice. f is not one of the available choices.'))

    def test_not_logged_in_user_cant_view_or_edit_profile(self):
        """
        Test that a user who isn't logged in can't view/edit an existing user's profile
        """
        # try to view profile
        response = self.client.get(reverse('users:profile', kwargs={'user_id': self.user.id}))
        self.assertTrue(
            response.content.decode(response.charset).__contains__('You don\'t have access to this profile'))

        # try to edit profile
        response = self.client.post(reverse('users:profile', kwargs={'user_id': self.user.id}),
                                    {
                                        'skill_level': 'c',
                                        'preferred_position': 'defense'
                                    },
                                    follow=True)
        self.user.refresh_from_db()
        self.assertTrue(self.user.skill_level == 'd')
        self.assertTrue(self.user.preferred_position == 'forward')
        self.assertTrue(
            response.content.decode(response.charset).__contains__('You don\'t have access to this profile'))

    def test_logged_in_user_cant_view_or_edit_other_users_profile(self):
        """
        Test that a user who is logged in can't view/edit another existing user's profile
        """
        # login as user
        self.client.post(self.loginURL, {'username': self.username, 'password': self.password}, follow=True)
        # try to view profile of user2
        response = self.client.get(reverse('users:profile', kwargs={'user_id': self.user2.id}))
        self.assertTrue(
            response.content.decode(response.charset).__contains__('You don\'t have access to this profile'))

        # try to edit profile of user2
        response = self.client.post(reverse('users:profile', kwargs={'user_id': self.user2.id}),
                                    {
                                        'skill_level': 'c',
                                        'preferred_position': 'defense'
                                    },
                                    follow=True)
        self.user.refresh_from_db()
        self.assertTrue(self.user.skill_level == 'd')
        self.assertTrue(self.user.preferred_position == 'forward')
        self.assertTrue(
            response.content.decode(response.charset).__contains__('You don\'t have access to this profile'))
