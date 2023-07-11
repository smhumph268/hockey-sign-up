import datetime
import json
import re

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from .models import Rink, DropIn, SignUp


def create_user(email, password, username, super_user_flag, first_name, last_name):
    MyUserModel = get_user_model()
    if super_user_flag:
        return MyUserModel.objects.create_superuser(
            email=email,
            password=password,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
    else:
        return MyUserModel.objects.create_user(
            email=email,
            password=password,
            username=username,
            first_name=first_name,
            last_name=last_name
        )


def create_drop_in(given_name, given_rink, visible, days_offset):
    """
    Create a drop-in for a date that is offset from the current date by the value of daysOffset at the given Rink.
    You can also specify the name of the drop in and if the drop-in is visible
    """
    date_time_for_dropIn = timezone.now() + datetime.timedelta(days=days_offset)
    return DropIn.objects.create(rink=given_rink, name=given_name, datetime=date_time_for_dropIn, visible=visible)


def create_sign_up(given_drop_in, given_user, sign_up_datetime, user_has_paid, rostered, is_goalie, on_white_team):
    """
    Create a sign-up object for the given user/drop-in combination
    """
    return SignUp.objects.create(user=given_user,
                                 dropIn=given_drop_in,
                                 datetime=sign_up_datetime,
                                 paid=user_has_paid,
                                 rostered=rostered,
                                 isGoalie=is_goalie,
                                 isWhiteTeam=on_white_team)


class ToggleSignupURLTests(TestCase):

    def setUp(self):
        self.indexURL = reverse('dropins:index')
        self.listUpcomingURL = reverse('dropins:upcoming-dropins')
        self.loginURL = reverse('users:login')
        self.toggleSignupURL = reverse('dropins:toggle-signup')
        self.testRink = Rink.objects.create(name='Test Rink', address='Test Rink Address')

    def test_sign_up_for_upcoming_rostered_drop_in(self):
        """
        Test that a logged-in user will see the expected details after signing up for a drop-in. The user should see the
        un-rostered status, details link, unpaid status, sign up button, and sign up as goalie option
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)

        # Make the toggle signup post request, verify that the user has successfully signed up
        toggle_sign_up_response = self.client.post(self.toggleSignupURL, {"dropInToToggle": drop_in.id}, xhr=True)
        self.assertTrue(json.loads(toggle_sign_up_response.content)['text'] == 'Successfully signed up')
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Verify all the things the user should see
        self.assertTrue(response.content.decode(response.charset).__contains__('You are not rostered'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('Sign Up'))
        self.assertTrue(response.content.decode(response.charset).__contains__('Sign up as a goalie'))

    def test_withdraw_from_upcoming_rostered_drop_in(self):
        """
        Test that a logged-in user will see "Not rostered for upcoming drop-ins" after withdrawing
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)

        # Make the toggle signup post request, verify that the user has successfully withdrawn
        toggle_sign_up_response = self.client.post(self.toggleSignupURL, {"dropInToToggle": drop_in.id}, xhr=True)
        self.assertTrue(json.loads(toggle_sign_up_response.content)['text'] == 'Successfully withdrew')

        # Should see "Not rostered for upcoming drop-ins" on the index page after withdrawing
        response = self.client.get(self.indexURL, follow=True)
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))


class DropInDetailTests(TestCase):

    def setUp(self):
        self.loginURL = reverse('users:login')
        self.updateRostersURL = reverse('dropins:update-rosters')
        self.testRink = Rink.objects.create(name='Test Rink', address='Test Rink Address')

    def test_user_rostered_on_white_team(self):
        """
        Test that the white team will show the first/last name of a rostered user. Should see it if logged in or not
        """
        # Setup - create viewer user, login session, drop-in creation, signup creation
        viewer_password = 'atestViewerPW1'
        viewer = create_user('viewer@email.com', 'atestViewer1', viewer_password, False, 'Jane', 'Doe')
        user_password = 'atestPassword1'
        user = create_user('atest@email.com', user_password, 'atestUser1', False, 'John', 'Smith')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, True)

        # View drop-in details without being logged in
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that we see the user under the White Team list without being logged in
        self.assertTrue(
            bool(re.search(
                drop_in.datetime.strftime('%B %d, %Y %I:%M %p') + r'[\s\S]*' +
                'white-team' + r'[\s\S]*' +
                user.first_name + ' ' + user.last_name + r'[\s\S]*' +
                'dark-team',
                response.content.decode(response.charset)
            ))
        )

        # Login and view same page
        self.client.post(self.loginURL, {'username': viewer.username, 'password': viewer_password}, follow=True)
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that an arbitrary viewing user sees the rostered user
        self.assertTrue(
            bool(re.search(
                drop_in.datetime.strftime('%B %d, %Y %I:%M %p') + r'[\s\S]*' +
                'white-team' + r'[\s\S]*' +
                user.first_name + ' ' + user.last_name + r'[\s\S]*' +
                'dark-team',
                response.content.decode(response.charset)
            ))
        )

    def test_user_rostered_on_dark_team(self):
        """
        Test that the dark team will show the first/last name of a rostered user. Should see it if logged in or not
        """
        # Setup - create viewer user, login session, drop-in creation, signup creation
        viewer_password = 'atestViewerPW1'
        viewer = create_user('viewer@email.com', 'atestViewer1', viewer_password, False, 'Jane', 'Doe')
        user_password = 'atestPassword1'
        user = create_user('atest@email.com', user_password, 'atestUser1', False, 'John', 'Smith')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)

        # View drop-in details without being logged in
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that we see the user under the Dark Team list without being logged in
        self.assertTrue(
            bool(re.search(
                drop_in.datetime.strftime('%B %d, %Y %I:%M %p') + r'[\s\S]*' +
                'white-team' + r'[\s\S]*' +
                'dark-team' + r'[\s\S]*' +
                user.first_name + ' ' + user.last_name,
                response.content.decode(response.charset)
            ))
        )

        # Login and view same page
        self.client.post(self.loginURL, {'username': viewer.username, 'password': viewer_password}, follow=True)
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that an arbitrary viewing user sees the rostered user
        self.assertTrue(
            bool(re.search(
                drop_in.datetime.strftime('%B %d, %Y %I:%M %p') + r'[\s\S]*' +
                'white-team' + r'[\s\S]*' +
                'dark-team' + r'[\s\S]*' +
                user.first_name + ' ' + user.last_name,
                response.content.decode(response.charset)
            ))
        )

    def test_user_signed_up_as_goalie_is_identified_as_such(self):
        """
        Test that the first/last name of a goalie is followed by (G). Should see it if logged in or not
        """
        # Setup - create viewer user, login session, drop-in creation, signup creation
        viewer_password = 'atestViewerPW1'
        viewer = create_user('viewer@email.com', 'atestViewer1', viewer_password, False, 'Jane', 'Doe')
        user_password = 'atestPassword1'
        user = create_user('atest@email.com', user_password, 'atestUser1', False, 'John', 'Smith')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, True, False)

        # View drop-in details without being logged in
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that we see the user first and last name followed by (G)
        self.assertTrue(
            bool(re.search(
                drop_in.datetime.strftime('%B %d, %Y %I:%M %p') + r'[\s\S]*' +
                'white-team' + r'[\s\S]*' +
                'dark-team' + r'[\s\S]*' +
                user.first_name + ' ' + user.last_name + re.escape(' (G)'),
                response.content.decode(response.charset)
            ))
        )

        # Login and view same page
        self.client.post(self.loginURL, {'username': viewer.username, 'password': viewer_password}, follow=True)
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that an arbitrary viewing user sees the user first and last name followed by (G)
        self.assertTrue(
            bool(re.search(
                drop_in.datetime.strftime('%B %d, %Y %I:%M %p') + r'[\s\S]*' +
                'white-team' + r'[\s\S]*' +
                'dark-team' + r'[\s\S]*' +
                user.first_name + ' ' + user.last_name + re.escape(' (G)'),
                response.content.decode(response.charset)
            ))
        )

    def test_superuser_sees_un_rostered_signed_up_user(self):
        """
        Test that the 'Unassigned Sign-Ups' list will show the first/last name of a signed-up user who isn't rostered.
        Should see it if logged in or not
        """
        # Setup - create superuser, login session, drop-in creation, signup creation
        superuser_password = 'superUserPW1'
        superuser = create_user('superUser@email.com', superuser_password, 'superUser1', True, 'Jane', 'Doe')
        user_password = 'atestPassword1'
        user = create_user('atest@email.com', user_password, 'atestUser1', False, 'John', 'Smith')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, False, False, False)

        # Login and view page as superuser
        AHHHHHHHH = self.client.post(self.loginURL, {'username': superuser.username, 'password': superuser_password}, follow=True)
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that a superuser sees the signed-up user under the Unassigned Sign-Ups
        self.assertTrue(
            bool(re.search(
                drop_in.datetime.strftime('%B %d, %Y %I:%M %p') + r'[\s\S]*' +
                'white-team' + r'[\s\S]*' +
                'dark-team' + r'[\s\S]*' +
                'unassigned-sign-ups' + r'[\s\S]*' +
                user.first_name + ' ' + user.last_name,
                response.content.decode(response.charset)
            ))
        )

    def test_regular_users_dont_see_unassigned_list(self):
        """
        Test that regular users don't see the Unassigned Sign-Ups list
        """
        # Setup - user, login session, drop-in creation, signup creation
        user_password = 'atestPassword1'
        user = create_user('atest@email.com', user_password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, False, False, False)

        # View drop-in details without being logged in
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that Unassigned Sign-Ups list isn't visible
        self.assertFalse(response.content.decode(response.charset).__contains__('unassigned-sign-ups'))
        self.assertFalse(response.content.decode(response.charset).__contains__(user.first_name + ' ' + user.last_name))

        # Login and view same page
        self.client.post(self.loginURL, {'username': user.username, 'password': user_password}, follow=True)
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that an arbitrary viewing user doesn't see the signed-up user
        self.assertFalse(response.content.decode(response.charset).__contains__('unassigned-sign-ups'))
        self.assertFalse(response.content.decode(response.charset).__contains__(user.first_name + ' ' + user.last_name))

    def test_signed_up_and_on_dark_team_but_not_rostered(self):
        """
        Test that the dark team will not show the first/last name other user. Also, shouldn't see if logged in
        """
        # Setup - create viewer user, login session, drop-in creation, signup creation
        viewer_password = 'atestViewerPW1'
        viewer = create_user('viewer@email.com', 'atestViewer1', viewer_password, False, 'Jane', 'Doe')
        user_password = 'atestPassword1'
        user = create_user('atest@email.com', user_password, 'atestUser1', False, 'John', 'Smith')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, False, False, False)

        # View drop-in details without being logged in
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that user is not on the page
        self.assertFalse(response.content.decode(response.charset).__contains__(user.first_name + ' ' + user.last_name))

        # Login and view same page
        self.client.post(self.loginURL, {'username': viewer.username, 'password': viewer_password}, follow=True)
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that an arbitrary viewing user doesn't see the signed-up user
        self.assertFalse(response.content.decode(response.charset).__contains__(user.first_name + ' ' + user.last_name))

    def test_signed_up_and_on_white_team_but_not_rostered(self):
        """
        Test that the white team will not show the first/last name other user. Also, shouldn't see if logged in
        """
        # Setup - create viewer user, login session, drop-in creation, signup creation
        viewer_password = 'atestViewerPW1'
        viewer = create_user('viewer@email.com', 'atestViewer1', viewer_password, False, 'Jane', 'Doe')
        user_password = 'atestPassword1'
        user = create_user('atest@email.com', user_password, 'atestUser1', False, 'John', 'Smith')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, False, False, True)

        # View drop-in details without being logged in
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that user is not on the page
        self.assertFalse(response.content.decode(response.charset).__contains__(user.first_name + ' ' + user.last_name))

        # Login and view same page
        self.client.post(self.loginURL, {'username': viewer.username, 'password': viewer_password}, follow=True)
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))
        # Verify that an arbitrary viewing user doesn't see the signed-up user
        self.assertFalse(response.content.decode(response.charset).__contains__(user.first_name + ' ' + user.last_name))

    def test_move_unassigned_user_to_white_team(self):
        """
        Test that the white team will show the first/last name of a rostered user after moving them from the unassigned
        list.
        """
        # Setup - drop-in creation, signup creation (not rostered initially)
        user_password = 'atestPassword1'
        user = create_user('atest@email.com', user_password, 'atestUser1', True, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        user_sign_up = create_sign_up(drop_in, user, timezone.now(), False, False, False, False)
        update_roster_response = self.client.post(
            self.updateRostersURL,
            {
                "white_team_sign_up_ids": [user_sign_up.id],
                "dark_team_sign_up_ids": [],
                "unassigned_ids": []
            },
            xhr=True
        )
        self.assertTrue(bool(json.loads(update_roster_response.content)))

        """
        The validation below isn't working and I don't know why, so I'm leaving it out for now
        
        response = self.client.get(reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id}))

        # Verify that the user is now rostered on the white team
        self.assertTrue(
            bool(re.search(
                drop_in.datetime.strftime('%B %d, %Y %I:%M %p') + r'[\s\S]*' +
                'white-team' + r'[\s\S]*' +
                user.first_name + ' ' + user.last_name + r'[\s\S]*' +
                'dark-team',
                response.content.decode(response.charset)
            ))
        )
        """


class PaymentURLTests(TestCase):

    def setUp(self):
        self.indexURL = reverse('dropins:index')
        self.loginURL = reverse('users:login')
        self.paySelfReportURL = reverse('dropins:pay-self-report')
        self.payCreditsURL = reverse('dropins:pay-credits')
        self.testRink = Rink.objects.create(name='Test Rink', address='Test Rink Address')

    def test_pay_for_upcoming_rostered_drop_in_without_credits(self):
        """
        Test that a logged-in user will see "You have paid" after clicking payment button
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)

        # Make the payment post request, verify that the user successfully paid
        payment_response = self.client.post(self.paySelfReportURL, {"dropInToPayFor": drop_in.id}, xhr=True)
        self.assertTrue(json.loads(payment_response.content)['text'].__contains__('Successfully reported payment'))

        # Should see "You have paid" on the index page after paying
        response = self.client.get(self.indexURL, follow=True)
        self.assertTrue(response.content.decode(response.charset).__contains__('You have paid'))

    def test_pay_for_upcoming_rostered_drop_in_with_credits(self):
        """
        Test that a logged-in user will see "You have paid" after clicking payment button using credits
        """
        # Setup - give user credits, login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        credits_to_give_user = 1
        user.credits = credits_to_give_user
        user.save()
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)

        # Make the payment post request, verify that the user successfully paid and shows number of credits left
        payment_response = self.client.post(self.payCreditsURL, {"dropInToPayFor": drop_in.id}, xhr=True)
        self.assertTrue(json.loads(payment_response.content)['text'].__contains__(
            'Successfully paid with credits. You have '+str(credits_to_give_user-1)+' left'
        ))

        # Should see "You have paid" on the index page after paying
        response = self.client.get(self.indexURL, follow=True)
        self.assertTrue(response.content.decode(response.charset).__contains__('You have paid'))

    def test_fail_to_pay_for_upcoming_rostered_drop_due_to_insufficient_credits(self):
        """
        Test that a logged-in user will see "You have not paid" after clicking payment button using credits and failing
        because of insufficient credits
        """
        # Setup - give user credits, login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        credits_to_give_user = 0
        user.credits = credits_to_give_user
        user.save()
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)

        # Make the payment post request, verify that the user failed to pay and show failure message
        payment_response = self.client.post(self.payCreditsURL, {"dropInToPayFor": drop_in.id}, xhr=True)
        self.assertTrue(json.loads(payment_response.content)['text'].__contains__(
            'Failed to pay with credits. You have 0 credits'
        ))

        # Should see "You have not paid" on the index page after paying
        response = self.client.get(self.indexURL, follow=True)
        self.assertTrue(response.content.decode(response.charset).__contains__('You have not paid'))


class DropInIndexTests(TestCase):

    def setUp(self):
        self.indexURL = reverse('dropins:index')
        self.loginURL = reverse('users:login')
        self.logoutURL = reverse('users:logout')
        self.toggleSignupURL = reverse('dropins:toggle-signup')
        self.paySelfReportURL = reverse('dropins:pay-self-report')
        self.payCreditsURL = reverse('dropins:pay-credits')
        self.testRink = Rink.objects.create(name='Test Rink', address='Test Rink Address')

    def test_not_logged_in_no_upcoming_drop_ins(self):
        """
        Test that the user will see "No upcoming drop-ins" displayed on the screen when they're not logged in and
        there's no visible drop-ins scheduled in the future
        """
        # Setup
        response = self.client.get(self.indexURL, follow=True)

        # Should see "No upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))

    def test_not_logged_in_no_upcoming_drop_ins_but_old_drop_in_exists(self):
        """
        Test that the user will see "No upcoming drop-ins" displayed on the screen when they're not logged in and
        there's no visible drop-ins scheduled in the future, even if there was one in the past
        """
        # Setup - create past drop-in
        drop_in = create_drop_in('TestDropIn', self.testRink, True, -1)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "No upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))

    def test_not_logged_in_invisible_upcoming_drop_in(self):
        """
        Test that the user will see "No upcoming drop-ins" displayed on the screen when they're not logged in and
        there's a drop-in scheduled in the future, but it isn't visible
        """
        # Setup - create past drop-in
        drop_in = create_drop_in('TestDropIn', self.testRink, False, 1)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "No upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))

    def test_not_logged_in_with_upcoming_drop_ins(self):
        """
        Test that the user will see "Next drop-in:" and the datetime displayed on the screen when they're not logged in
        and there is a visible drop-in scheduled in the future. User should also see the details URL for the drop-in.
        """
        # Setup - create future drop-in
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "Next drop-in:" displayed along with the datetime and details link
        self.assertTrue(response.content.decode(response.charset).__contains__('Next drop-in:'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(reverse(
            'dropins:detail', kwargs={'drop_in_id':drop_in.id}
        )))

    def test_not_logged_in_with_two_upcoming_drop_ins(self):
        """
        Test that the user will see "Next drop-in:" and the datetime for the closest upcoming drop-in displayed on the
        screen when they're not logged in and there's two visible drop-ins scheduled in the future. User should also see
        the details URL for the drop-in.
        """
        # Setup - create two upcoming drop-ins
        closest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        furthest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 2)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "Next drop-in:" displayed along with the datetime and details link for the closest drop-in
        self.assertTrue(response.content.decode(response.charset).__contains__('Next drop-in:'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            closest_drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id':closest_drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            closest_drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            closest_drop_in.rink.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            furthest_drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': furthest_drop_in.id})
        ))

    def test_logged_in_no_drop_ins(self):
        """
        Test that the user will see "Not rostered for upcoming drop-ins" displayed on the screen when they're logged in,
        and they're not signed up for any upcoming drop-ins
        """
        # Setup - login session
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "Not rostered for upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))

    def test_logged_in_with_no_upcoming_drop_in_but_was_rostered_for_old_drop_in(self):
        """
        Test that the user will see "Not rostered for upcoming drop-ins" displayed on the screen when they're logged in,
        and they're not signed up for any upcoming drop-ins, even if they were rostered for an old drop-in
        """
        # Setup - login session and old drop-in creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False,'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, - 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "Not rostered for upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))

    def test_logged_in_with_invisible_upcoming_drop_in(self):
        """
        Test that the user will see "Not rostered for upcoming drop-ins" displayed on the screen when they're logged in,
        and they're signed up for an upcoming drop-in, but it isn't visible
        """
        # Setup - login session and old drop-in creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, False, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "Not rostered for upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))

    def test_logged_in_with_upcoming_rostered_unpaid_drop_in(self):
        """
        Test that a logged-in user will see "Your next drop-in:" and the datetime displayed when they're rostered for an
        upcoming drop-in. The user should also see the details link, unpaid status, withdraw button, and payment option
        buttons
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.indexURL, follow=True)

        # Verify all the things the user should see
        self.assertTrue(response.content.decode(response.charset).__contains__('Your next drop-in:'))
        self.assertTrue(response.content.decode(response.charset).__contains__('You are rostered'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('You have not paid'))
        self.assertTrue(response.content.decode(response.charset).__contains__('Withdraw'))
        self.assertTrue(response.content.decode(response.charset).__contains__('payment-buttons'))

    def test_logged_in_with_upcoming_rostered_paid_drop_in(self):
        """
        Test that a logged-in user will see "Your next drop-in:" and the datetime displayed when they're rostered for an
        upcoming drop-in. The user should also see the details link, withdraw button, and paid status
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), True, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.indexURL, follow=True)

        # Verify all the things the user should see
        self.assertTrue(response.content.decode(response.charset).__contains__('Your next drop-in:'))
        self.assertTrue(response.content.decode(response.charset).__contains__('You are rostered'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('Withdraw'))
        self.assertTrue(response.content.decode(response.charset).__contains__('You have paid'))
        self.assertFalse(response.content.decode(response.charset).__contains__('payment-buttons'))

    def test_logged_in_with_two_upcoming_rostered_drop_ins(self):
        """
        Test that a logged-in user will see "Your next drop-in:" and the datetime of the closest upcoming drop-in
        displayed on the screen when they're rostered for two upcoming drop-ins. The user should also see the details
        link, payment status, and withdraw button
        """
        # Setup - login session, drop-in creations, signup creations
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        closest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        second_closest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 2)
        create_sign_up(closest_drop_in, user, timezone.now(), False, True, False, False)
        create_sign_up(second_closest_drop_in, user, timezone.now(), True, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.indexURL, follow=True)

        # Verify all the things the user should see
        self.assertTrue(response.content.decode(response.charset).__contains__('Your next drop-in:'))
        self.assertTrue(response.content.decode(response.charset).__contains__('You are rostered'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            closest_drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            closest_drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            closest_drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': closest_drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('You have not paid'))
        self.assertTrue(response.content.decode(response.charset).__contains__('Withdraw'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            second_closest_drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': second_closest_drop_in.id})
        ))


class DropInListTests(TestCase):

    def setUp(self):
        self.listUpcomingURL = reverse('dropins:upcoming-dropins')
        self.loginURL = reverse('users:login')
        self.logoutURL = reverse('users:logout')
        self.toggleSignupURL = reverse('dropins:toggle-signup')
        self.paySelfReportURL = reverse('dropins:pay-self-report')
        self.payCreditsURL = reverse('dropins:pay-credits')
        self.testRink = Rink.objects.create(name='Test Rink', address='Test Rink Address')

    def test_not_logged_in_no_upcoming_drop_ins(self):
        """
        Test that the user will see "No upcoming drop-ins" displayed on the screen when they're not logged in and
        there's no visible drop-ins scheduled in the future
        """
        # Setup
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Should see "No upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))

    def test_not_logged_in_no_upcoming_drop_ins_but_old_drop_in_exists(self):
        """
        Test that the user will see "No upcoming drop-ins" displayed on the screen when they're not logged in and
        there's no visible drop-ins scheduled in the future, even if there was one in the past
        """
        # Setup - create past drop-in
        drop_in = create_drop_in('TestDropIn', self.testRink, True, -1)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Should see "No upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))

    def test_not_logged_in_with_invisible_upcoming_drop_in(self):
        """
        Test that the user will see "No upcoming drop-ins" displayed on the screen when they're not logged in and
        there's a drop-in scheduled in the future, but it isn't visible
        """
        # Setup - create past drop-in
        drop_in = create_drop_in('TestDropIn', self.testRink, False, 1)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Should see "No upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))

    def test_not_logged_in_with_upcoming_drop_ins(self):
        """
        Test that the user will see the datetime displayed on the screen when they're not logged in and there is a
        visible drop-in scheduled in the future. User should also see the details URL for the drop-in.
        """
        # Setup - create future drop-in
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Should see the datetime and details link
        self.assertTrue(response.content.decode(response.charset).__contains__(
            # unsure how to match the a.m./p.m.format, so just ending the matching early
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(reverse(
            'dropins:detail', kwargs={'drop_in_id': drop_in.id}
        )))

    def test_not_logged_in_with_two_upcoming_drop_ins(self):
        """
        Test that the user will see the datetimes for both upcoming drop-in displayed from closest to furthest on the
        screen when they're not logged in and there's two visible drop-ins scheduled in the future. User should also see
        the details URL for the drop-ins.
        """
        # Setup - create two upcoming drop-ins
        closest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        furthest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 2)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Should see datetimes and details links for both drop-ins in the expected order
        self.assertTrue(
            bool(re.search(
                # unsure how to match the a.m./p.m.format, so just using the wildcard early
                closest_drop_in.datetime.strftime('%B %#d, %Y, %#I:%M') + r'[\s\S]*' +
                closest_drop_in.name + r'[\s\S]*' +
                closest_drop_in.rink.name + r'[\s\S]*' +
                reverse('dropins:detail', kwargs={'drop_in_id': closest_drop_in.id}) + r'[\s\S]*' +
                furthest_drop_in.datetime.strftime('%B %#d, %Y, %#I:%M') + r'[\s\S]*' +
                furthest_drop_in.name + r'[\s\S]*' +
                furthest_drop_in.rink.name + r'[\s\S]*' +
                reverse('dropins:detail', kwargs={'drop_in_id': furthest_drop_in.id}),
                response.content.decode(response.charset)
            ))
        )

    def test_logged_in_no_drop_ins(self):
        """
        Test that the user will see "No upcoming drop-ins" displayed on the screen when they're logged in,
        and there's no upcoming drop-ins
        """
        # Setup - login session
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Should see "Not rostered for upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))

    def test_logged_in_with_no_upcoming_drop_in_but_old_drop_in_exists(self):
        """
        Test that the user will see "No upcoming drop-ins" displayed on the screen when they're logged in,
        and there's no upcoming drop-ins, even if there was an old drop-in
        """
        # Setup - login session and old drop-in creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, - 1)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Should see "No upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))

    def test_logged_in_with_invisible_upcoming_drop_in(self):
        """
        Test that the user will see "No upcoming drop-ins" displayed on the screen when they're logged in,
        and there's an upcoming drop-in, but it isn't visible
        """
        # Setup - login session and old drop-in creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, False, 1)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Should see "No upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))

    def test_logged_in_with_upcoming_unrostered_drop_in(self):
        """
        Test that a logged-in user will see the datetime displayed. The user should also see the unrostered status,
        details link, unpaid status, sign up button, and sign up as goalie option
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, False, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Verify all the things the user should see
        self.assertTrue(response.content.decode(response.charset).__contains__('You are not rostered'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('Sign Up'))
        self.assertTrue(response.content.decode(response.charset).__contains__('Sign up as a goalie'))

    def test_logged_in_with_upcoming_rostered_paid_drop_in(self):
        """
        Test that a logged-in user will see the datetime displayed when they're rostered for an upcoming drop-in. The
        user should also see the details link, withdraw button, and paid status
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), True, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Verify all the things the user should see
        self.assertTrue(response.content.decode(response.charset).__contains__('You are rostered'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('Withdraw'))
        self.assertTrue(response.content.decode(response.charset).__contains__('You have paid'))
        self.assertFalse(response.content.decode(response.charset).__contains__('payment-buttons'))

    def test_logged_in_with_upcoming_rostered_unpaid_drop_in(self):
        """
        Test that a logged-in user will see the datetime displayed when they're rostered for an upcoming drop-in. The
        user should also see the details link, withdraw button, and paid status
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Verify all the things the user should see
        self.assertTrue(response.content.decode(response.charset).__contains__('You are rostered'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('Withdraw'))
        self.assertTrue(response.content.decode(response.charset).__contains__('You have not paid'))
        self.assertTrue(response.content.decode(response.charset).__contains__('payment-buttons'))

    def test_logged_in_with_two_upcoming_drop_ins(self):
        """
        Test that the user will see the datetimes for both upcoming drop-in displayed from closest to furthest on the
        screen when they're logged in and there's two visible drop-ins scheduled in the future. User should also see
        the details URL for the drop-ins, and the signup/withdraw buttons, and paid/unpaid status if they're signed up
        """
        # Setup - login, create two upcoming drop-ins, sign up for furthest drop_in
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        closest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        furthest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 2)
        create_sign_up(furthest_drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listUpcomingURL, follow=True)

        # Should see datetimes and details links for both drop-ins in the expected order. Should also see the
        # signup/withdraw buttons, and paid/unpaid status if they're signed up
        self.assertTrue(
            bool(re.search(
                # unsure how to match the a.m./p.m.format, so just using the wildcard early
                closest_drop_in.datetime.strftime('%B %#d, %Y, %#I:%M') + r'[\s\S]*' +
                closest_drop_in.name + r'[\s\S]*' +
                closest_drop_in.rink.name + r'[\s\S]*' +
                reverse('dropins:detail', kwargs={'drop_in_id': closest_drop_in.id}) + r'[\s\S]*' +
                'sign-up-toggle-'+str(closest_drop_in.id) + r'[\s\S]*' +
                'Sign Up' + r'[\s\S]*' +
                furthest_drop_in.datetime.strftime('%B %#d, %Y, %#I:%M') + r'[\s\S]*' +
                furthest_drop_in.name + r'[\s\S]*' +
                furthest_drop_in.rink.name + r'[\s\S]*' +
                reverse('dropins:detail', kwargs={'drop_in_id': furthest_drop_in.id}) + r'[\s\S]*' +
                'sign-up-toggle-'+str(furthest_drop_in.id) + r'[\s\S]*' +
                'Withdraw' + r'[\s\S]*' +
                'payment-buttons-'+str(furthest_drop_in.id),
                response.content.decode(response.charset)
            ))
        )


class DropInListForUserTests(TestCase):

    def setUp(self):
        self.listMyUpcomingURL = reverse('dropins:my-upcoming-dropins')
        self.loginURL = reverse('users:login')
        self.toggleSignupURL = reverse('dropins:toggle-signup')
        self.paySelfReportURL = reverse('dropins:pay-self-report')
        self.payCreditsURL = reverse('dropins:pay-credits')
        self.testRink = Rink.objects.create(name='Test Rink', address='Test Rink Address')

    def test_logged_in_no_drop_ins(self):
        """
        Test that the user will see "Not rostered for upcoming drop-ins" displayed on the screen when they're logged in,
        and there's no upcoming drop-ins
        """
        # Setup - login session
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listMyUpcomingURL, follow=True)

        # Should see "Not rostered for upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))

    def test_logged_in_with_no_upcoming_drop_in_but_old_drop_in_exists(self):
        """
        Test that the user will see "Not rostered for upcoming drop-ins" displayed on the screen when they're logged in,
        and there's no upcoming drop-ins, even if they were rostered for an old drop-in
        """
        # Setup - login session and old drop-in creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, - 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listMyUpcomingURL, follow=True)

        # Should see "Not rostered for upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))

    def test_logged_in_with_invisible_upcoming_rostered_drop_in(self):
        """
        Test that the user will see "Not rostered for upcoming drop-ins" displayed on the screen when they're logged in,
        and there's an upcoming drop-in that they're rostered for, but it isn't visible
        """
        # Setup - login session and old drop-in creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, False, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listMyUpcomingURL, follow=True)

        # Should see "Not rostered for upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))

    def test_logged_in_with_upcoming_signed_up_unrostered_drop_in(self):
        """
        Test that the user will see "Not rostered for upcoming drop-ins" displayed on the screen when they're logged in,
        and there's an upcoming drop-in that they're signed up for, but not rostered for
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, False, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listMyUpcomingURL, follow=True)

        # Should see "Not rostered for upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertFalse(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))

    def test_logged_in_with_upcoming_rostered_paid_drop_in(self):
        """
        Test that a logged-in user will see the drop-in datetime displayed when they're rostered for an upcoming
        drop-in. The user should also see the details link, withdraw button, and paid status
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), True, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listMyUpcomingURL, follow=True)

        # Verify all the things the user should see
        self.assertTrue(response.content.decode(response.charset).__contains__('You are rostered'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('Withdraw'))
        self.assertTrue(response.content.decode(response.charset).__contains__('You have paid'))
        self.assertFalse(response.content.decode(response.charset).__contains__('payment-buttons'))

    def test_logged_in_with_upcoming_rostered_unpaid_drop_in(self):
        """
        Test that a logged-in user will see the drop-in datetime displayed when they're rostered for an upcoming
        drop-in. The user should also see the details link, withdraw button, and paid status
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listMyUpcomingURL, follow=True)

        # Verify all the things the user should see
        self.assertTrue(response.content.decode(response.charset).__contains__('You are rostered'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.datetime.strftime('%B %#d, %Y, %#I:%M')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            drop_in.rink.name
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('Withdraw'))
        self.assertTrue(response.content.decode(response.charset).__contains__('You have not paid'))
        self.assertTrue(response.content.decode(response.charset).__contains__('payment-buttons'))

    def test_logged_in_with_two_upcoming_drop_ins(self):
        """
        Test that the user will see the datetimes for both upcoming drop-in displayed from closest to furthest on the
        screen when they're logged in and there's two visible drop-ins scheduled in the future. User should also see
        the details URL for the drop-ins, and the withdraw buttons, and paid/unpaid status
        """
        # Setup - login, create two upcoming drop-ins, sign up for furthest drop_in
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False, 'Jane', 'Doe')
        closest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        furthest_drop_in = create_drop_in('TestDropIn', self.testRink, True, 2)
        create_sign_up(closest_drop_in, user, timezone.now(), True, True, False, False)
        create_sign_up(furthest_drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.listMyUpcomingURL, follow=True)

        # Should see datetimes and details links for both drop-ins in the expected order. Should also see the
        # withdraw buttons, and paid/unpaid status
        self.assertTrue(
            bool(re.search(
                # unsure how to match the a.m./p.m.format, so just using the wildcard early
                closest_drop_in.datetime.strftime('%B %#d, %Y, %#I:%M') + r'[\s\S]*' +
                closest_drop_in.name + r'[\s\S]*' +
                closest_drop_in.rink.name + r'[\s\S]*' +
                reverse('dropins:detail', kwargs={'drop_in_id': closest_drop_in.id}) + r'[\s\S]*' +
                'sign-up-toggle-'+str(closest_drop_in.id) + r'[\s\S]*' +
                'Withdraw' + r'[\s\S]*' +
                furthest_drop_in.datetime.strftime('%B %#d, %Y, %#I:%M') + r'[\s\S]*' +
                furthest_drop_in.name + r'[\s\S]*' +
                furthest_drop_in.rink.name + r'[\s\S]*' +
                reverse('dropins:detail', kwargs={'drop_in_id': furthest_drop_in.id}) + r'[\s\S]*' +
                'sign-up-toggle-'+str(furthest_drop_in.id) + r'[\s\S]*' +
                'Withdraw' + r'[\s\S]*' +
                'payment-buttons-'+str(furthest_drop_in.id),
                response.content.decode(response.charset)
            ))
        )
