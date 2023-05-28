from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.db import transaction
from django.views import generic
from django.utils import timezone
from django.http import JsonResponse

from .models import DropIn, SignUp


class IndexView(generic.ListView):
    template_name = 'dropins/index.html'
    context_object_name = 'upcoming_dropin'

    def get_queryset(self):
        """
        Shows next upcoming drop-in. If logged in, shows the next upcoming drop-in that the user is rostered for.
        """
        if self.request.user.is_authenticated:
            rostered_signups = SignUp.objects.filter(user=self.request.user, rostered=True)
            return DropIn.objects.filter(
                datetime__gte=timezone.now(),
                visible=True,
                id__in=rostered_signups.values_list('dropIn', flat=True)
            ).order_by('datetime')[:1]
        else:
            return DropIn.objects.filter(
                datetime__gte=timezone.now(),
                visible=True
            ).order_by('datetime')[:1]


def list_upcoming(request):
    """
    Shows upcoming drop-ins. Passing in the user's signups as well so that we can show buttons to sign up or
    withdraw from a drop-in.
    """
    drop_ins = DropIn.objects.filter(
        datetime__gte=timezone.now(),
        visible=True
    ).order_by('datetime')
    paginator = Paginator(drop_ins, 5)  # Show 5 drop-ins per page.

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.user.is_authenticated:
        users_sign_ups = SignUp.objects.filter(
            user=request.user,
            dropIn__in=drop_ins.values_list('id', flat=True)
        )

        users_rostered_sign_ups = SignUp.objects.filter(
            user=request.user,
            dropIn__in=drop_ins.values_list('id', flat=True),
            rostered=True
        )

        return render(
            request,
            'dropins/dropin_list.html',
            {
              "page_obj": page_obj,
              'users_drop_ins': users_sign_ups.values_list('dropIn', flat=True),
              'users_rostered_drop_ins': users_rostered_sign_ups.values_list('dropIn', flat=True)
            }
        )
    else:
        return render(
            request,
            'dropins/dropin_list.html',
            {
                "page_obj": page_obj
            }
        )


def list_my_upcoming(request):
    """
    Shows upcoming drop-ins that a user is signed up and rostered for. Passing in the user's signups as well so that we
    can show buttons to sign up or withdraw from a drop-in.
    """
    rostered_signups = SignUp.objects.filter(user=request.user, rostered=True)
    drop_ins = DropIn.objects.filter(
        datetime__gte=timezone.now(),
        visible=True,
        id__in=rostered_signups.values_list('dropIn', flat=True)
    ).order_by('datetime')
    paginator = Paginator(drop_ins, 5)  # Show 5 drop-ins per page.

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Only visitors who are signed in should be able to see the link to this page
    if request.user.is_authenticated:
        users_drop_ins = SignUp.objects.filter(
            user=request.user,
            dropIn__in=drop_ins.values_list('id', flat=True)
        )

        return render(
            request,
            'dropins/dropin_list.html',
            {
                "page_obj": page_obj,
                'users_drop_ins': users_drop_ins.values_list('dropIn', flat=True),
                # The user should be rostered for all users_drop_ins based on the logic above
                'users_rostered_drop_ins': users_drop_ins.values_list('dropIn', flat=True)
            }
        )
    else:
        return render(
            request,
            'dropins/dropin_list.html',
            {
                "page_obj": page_obj
            }
        )


def single_drop_in_detail_view(request, drop_in_id):
    drop_in = get_object_or_404(DropIn, pk=drop_in_id)
    signups = SignUp.objects.filter(dropIn=drop_in_id)
    return render(request, 'dropins/dropin_detail.html', {'drop_in': drop_in, 'signups': signups})


def update_rosters(request):
    if request.method == 'POST':
        white_team_sign_up_ids = request.POST.getlist('white_team_sign_up_ids[]')
        dark_team_sign_up_ids = request.POST.getlist('dark_team_sign_up_ids[]')
        unassigned_ids = request.POST.getlist('unassigned_ids[]')

        for signup_id in white_team_sign_up_ids:
            player_signup = SignUp.objects.select_for_update().get(pk=signup_id)
            with transaction.atomic():
                player_signup.isWhiteTeam = True
                player_signup.rostered = True
                player_signup.save()

        for signup_id in dark_team_sign_up_ids:
            player_signup = SignUp.objects.select_for_update().get(pk=signup_id)
            with transaction.atomic():
                player_signup.isWhiteTeam = False
                player_signup.rostered = True
                player_signup.save()

        for signup_id in unassigned_ids:
            player_signup = SignUp.objects.select_for_update().get(pk=signup_id)
            with transaction.atomic():
                player_signup.rostered = False
                player_signup.save()

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})


def toggle_signup(request):
    if request.method == 'POST':
        drop_in = get_object_or_404(DropIn, pk=request.POST.get('dropInToToggle'))
        user_signups_for_drop_in = SignUp.objects.filter(user=request.user.id, dropIn=drop_in.id)
        action = 'signed up'

        if user_signups_for_drop_in:
            user_signups_for_drop_in.delete()
            action = 'withdrew'
        else:
            new_sign_up = SignUp(
                user=request.user,
                dropIn=drop_in,
                datetime=timezone.now(),
                isGoalie=request.POST.get('asGoalie') == 'true'
            )
            new_sign_up.save()

        return JsonResponse({'success': True, 'text': 'Successfully '+action})
    else:
        return JsonResponse({'success': False})
