# django packages
from django.urls import path

# local app
from .field_views import NewReviewFieldView, EditFieldsView, FieldReviewView
from .list_views import MappingAllListView, NewListView, MappingListView, ListDeleteView
from .views import AllMappingsView, NewMappingView, JoinMappingView, MappingView, MappingDeleteView


urlpatterns = [
    path('all/', AllMappingsView.as_view(), name="mapping_all"),
    path('new/', NewMappingView.as_view(), name="mapping_new"),
    path('join/', JoinMappingView.as_view(), name="mapping_join"),
    path('view/<int:mapping_id>/', MappingView.as_view(), name="mapping"),
    path('delete_mapping/<int:mapping_id>/', MappingDeleteView.as_view(), name="mapping_delete"),

    path('view/<int:mapping_id>/lists/all', MappingAllListView.as_view(),name="publication_list_all"),
    path('view/<int:mapping_id>/lists/new', NewListView.as_view(), name="publication_list_new"),
    path('view/<int:mapping_id>/lists/view/<int:list_id>/', MappingListView.as_view(), name="publication_list"),
    path('view/<int:mapping_id>/lists/delete/<int:list_id>/', ListDeleteView.as_view(), name="publication_list_delete"),

    path("view/<int:mapping_id>/lists/view/<int:list_id>/field/new", NewReviewFieldView.as_view(), name="field_new"),
    path("view/<int:mapping_id>/lists/view/<int:list_id>/field/edit", EditFieldsView.as_view(), name="field_edit"),
    path("view/<int:mapping_id>/lists/view/<int:list_id>/field/review", FieldReviewView.as_view(), name="field_review"),
]