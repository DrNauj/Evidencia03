"""
URL configuration for bankprocessor project.
]
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from processor import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('process/', views.process_data, name='process_data'),
    path('results/', views.view_results, name='view_results'),
    path('results/<int:job_id>/', views.view_results, name='view_results_job'),
    path('history/', views.job_history, name='job_history'),
    path('history/delete/<int:job_id>/', views.job_delete, name='job_delete'),
    path('history/terminate/<int:job_id>/', views.job_terminate, name='job_terminate'),
    path('history/resume/<int:job_id>/', views.job_resume, name='job_resume'),
    path('history/clear/', views.job_clear_history, name='job_clear_history'),
    path('api/status/', views.processing_status, name='processing_status'),
    path('api/results/', views.processing_results_json, name='processing_results_json'),
]
