from django.shortcuts import get_object_or_404, render
from django.db import transaction
from django.views import generic
from django.utils import timezone
from django.http import JsonResponse

from .models import DropIn, SignUp


class IndexView(generic.ListView):
    template_name = 'dropins/index.html'
    context_object_name = 'upcoming_dropins'

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
            ).order_by('-datetime')[:1]
        else:
            return DropIn.objects.filter(
                datetime__gte=timezone.now(),
                visible=True
            ).order_by('-datetime')[:1]


def single_drop_in_detail_view(request, drop_in_id):
    drop_in = get_object_or_404(DropIn, pk=drop_in_id)
    signups = SignUp.objects.filter(dropIn=drop_in_id)
    # TODO: render different page if user is super user?
    return render(request, 'dropins/dropinDetail.html', {'drop_in': drop_in, 'signups': signups})


def update_rosters(request):
    if request.method == 'POST':
        drop_in_id = request.POST.get('drop_in_id')
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
