from django.urls import path
from . import views

app_name = 'dropins'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    # The SingleDropInDetailView generic view expects the primary key value captured from the URL to be called "pk"
    path('<int:drop_in_id>/', views.single_drop_in_detail_view, name='detail'),
    path('update-rosters/', views.update_rosters, name='update-rosters'),
    path('toggle-signup/', views.toggle_signup, name='toggle-signup'),
    path('list/upcoming/', views.list_upcoming, name='upcoming-dropins'),
    path('list/my-upcoming/', views.list_my_upcoming, name='my-upcoming-dropins')
]
