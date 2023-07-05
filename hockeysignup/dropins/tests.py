import datetime
import json

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from .models import Rink, DropIn, SignUp


def create_user(email, password, username, superUserFlag):
    MyUserModel = get_user_model()
    if superUserFlag:
        return MyUserModel.objects.create_super_user(email=email, password=password, username=username)
    else:
        return MyUserModel.objects.create_user(email=email, password=password, username=username)


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


class DropInIndexTests(TestCase):

    def setUp(self):
        self.indexURL = reverse('dropins:index')
        self.loginURL = reverse('users:login')
        self.logoutURL = reverse('users:logout')
        self.toggleSignupURL = reverse('dropins:toggle-signup')
        self.payPaypalURL = reverse('dropins:pay-paypal')
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
        create_drop_in('TestDropIn', self.testRink, True, -1)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "No upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('No upcoming drop-ins'))

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
        create_drop_in('TestDropIn', self.testRink, True, 2)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "Next drop-in:" displayed along with the datetime and details link for the closest drop-in
        self.assertTrue(response.content.decode(response.charset).__contains__('Next drop-in:'))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            closest_drop_in.datetime.strftime('%B %d, %Y %I:%M %p')
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__(
            reverse('dropins:detail', kwargs={'drop_in_id':closest_drop_in.id})
        ))

    def test_logged_in_no_drop_ins(self):
        """
        Test that the user will see "Not rostered for upcoming drop-ins" displayed on the screen when they're logged in,
        and they're not signed up for any upcoming drop-ins
        """
        # Setup - login session
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False)
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
        user = create_user('atest@email.com', password, 'atestUser1', False)
        drop_in = create_drop_in('TestDropIn', self.testRink, True, - 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)
        response = self.client.get(self.indexURL, follow=True)

        # Should see "Not rostered for upcoming drop-ins" displayed on the screen
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))

    def test_logged_in_with_upcoming_rostered_unpaid_drop_in(self):
        """
        Test that a logged-in user will see "Your next drop-in:" and the datetime displayed when they're rostered for an
        upcoming drop-in. The user should also see the details link, unpaid status, withdraw button, and payment option
        buttons
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False)
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
        user = create_user('atest@email.com', password, 'atestUser1', False)
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
            reverse('dropins:detail', kwargs={'drop_in_id': drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('Withdraw'))
        self.assertTrue(response.content.decode(response.charset).__contains__('You have paid'))

    def test_logged_in_with_two_upcoming_rostered_drop_ins(self):
        """
        Test that a logged-in user will see "Your next drop-in:" and the datetime of the closest upcoming drop-in
        displayed on the screen when they're rostered for two upcoming drop-ins. The user should also see the details
        link, payment status, and withdraw button
        """
        # Setup - login session, drop-in creations, signup creations
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False)
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
            reverse('dropins:detail', kwargs={'drop_in_id': closest_drop_in.id})
        ))
        self.assertTrue(response.content.decode(response.charset).__contains__('You have not paid'))
        self.assertTrue(response.content.decode(response.charset).__contains__('Withdraw'))

    def test_withdraw_from_upcoming_rostered_drop_in(self):
        """
        Test that a logged-in user will see "Not rostered for upcoming drop-ins" after withdrawing
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False)
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)

        # Make the toggle signup post request, verify that the user has successfully withdrawn
        toggle_sign_up_response = self.client.post(self.toggleSignupURL, {"dropInToToggle": drop_in.id}, xhr=True)
        self.assertTrue(json.loads(toggle_sign_up_response.content)['text'] == 'Successfully withdrew')

        # Should see "Not rostered for upcoming drop-ins" on the index page after withdrawing
        response = self.client.get(self.indexURL, follow=True)
        self.assertTrue(response.content.decode(response.charset).__contains__('Not rostered for upcoming drop-ins'))

    def test_pay_for_upcoming_rostered_drop_in_without_credits(self):
        """
        Test that a logged-in user will see "You have paid" after clicking payment button
        """
        # Setup - login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False)
        drop_in = create_drop_in('TestDropIn', self.testRink, True, 1)
        create_sign_up(drop_in, user, timezone.now(), False, True, False, False)
        self.client.post(self.loginURL, {'username': user.username, 'password': password}, follow=True)

        # Make the payment post request, verify that the user successfully paid
        payment_response = self.client.post(self.payPaypalURL, {"dropInToPayFor": drop_in.id}, xhr=True)
        self.assertTrue(json.loads(payment_response.content)['text'].__contains__('Successfully paid'))

        # Should see "You have paid" on the index page after paying
        response = self.client.get(self.indexURL, follow=True)
        self.assertTrue(response.content.decode(response.charset).__contains__('You have paid'))

    def test_pay_for_upcoming_rostered_drop_in_with_credits(self):
        """
        Test that a logged-in user will see "You have paid" after clicking payment button using credits
        """
        # Setup - give user credits, login session, drop-in creation, signup creation
        password = 'atestPassword1'
        user = create_user('atest@email.com', password, 'atestUser1', False)
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
        user = create_user('atest@email.com', password, 'atestUser1', False)
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
