from django.urls import path
from . import views

app_name = 'dropins'
urlpatterns = [
    path('', views.index, name='index'),
    # SingleDropInDetailView generic view expects the primary key value captured from the URL to be called "drop_in_id"
    path('<int:drop_in_id>/', views.single_drop_in_detail_view, name='detail'),
    path('update-rosters/', views.update_rosters, name='update-rosters'),
    path('toggle-signup/', views.toggle_signup, name='toggle-signup'),
    path('pay-self-report/', views.self_report_payment, name='pay-self-report'),
    path('pay-credits/', views.pay_with_credits, name='pay-credits'),
    path('list/upcoming/', views.list_upcoming, name='upcoming-dropins'),
    path('list/my-upcoming/', views.list_my_upcoming, name='my-upcoming-dropins')
]
