from rest_framework import serializers
from .models import Source, Country, Affiliation, Author, Venue, Keyword, Publication, FullText


class SourceSerializer(serializers.HyperlinkedModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name="retrieve_source_detail", read_only=True)
    publications = serializers.HyperlinkedRelatedField(
        view_name="retrieve_publication_detail", read_only=True, many=True)

    class Meta:
        model = Source
        fields = ['id', 'api_url', 'name', 'publications']


class CountrySerializer(serializers.HyperlinkedModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name="retrieve_country_detail", read_only=True)

    institutes = serializers.HyperlinkedRelatedField(
        view_name="retrieve_affiliation_detail", read_only=True, many=True)

    class Meta:
        model = Country
        fields = ['id', 'api_url', 'name', 'institutes']


class AffiliationSerializer(serializers.HyperlinkedModelSerializer):
    country = CountrySerializer()

    authors = serializers.HyperlinkedRelatedField(
        view_name="retrieve_author_detail", read_only=True, many=True)

    class Meta:
        model = Affiliation
        fields = ['id', 'institute', 'country', 'authors']


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name="retrieve_author_detail", read_only=True)
    published_papers = serializers.HyperlinkedRelatedField(
        view_name="retrieve_publication_detail", read_only=True, many=True)
    affiliation = AffiliationSerializer()
    class Meta:
        model = Author
        fields = ['id', 'api_url', 'first_name', 'last_name', 'ORCID',
                  'affiliation', 'published_papers']


class VenueSerializer(serializers.HyperlinkedModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name="retrieve_venue_detail", read_only=True)
    papers = serializers.HyperlinkedRelatedField(
        view_name="retrieve_publication_detail", read_only=True, many=True)

    venue_type = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Venue
        fields = ['id', 'api_url', 'name', 'venue_type', 'type', 'publisher', 'volume',
                  'issue', 'papers']


class KeywordSerializer(serializers.HyperlinkedModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name="retrieve_keyword_detail", read_only=True)
    related_papers = serializers.HyperlinkedRelatedField(
        view_name="retrieve_publication_detail", read_only=True, many=True)

    class Meta:
        model = Keyword
        fields = ['id', 'api_url', 'keyword', 'related_papers']


class PublicationSerializer(serializers.HyperlinkedModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name="retrieve_publication_detail", read_only=True)

    full_texts = serializers.HyperlinkedRelatedField(
        view_name="retrieve_full-text_detail", read_only=True, many=True)

    source = SourceSerializer()

    venue = VenueSerializer()

    authors = AuthorSerializer(many=True)

    keywords = KeywordSerializer(many=True)

    class Meta:
        model = Publication
        fields = ['id', 'api_url', 'doi', 'title', 'authors', 'keywords', 'year',
                  'datetime_added', 'abstract', 'full_texts', 'source', 'venue', 'first_created', 'last_update']


class FullTextSerializer(serializers.HyperlinkedModelSerializer):
    publication = PublicationSerializer()
    full_text_status = serializers.CharField(source='get_status_display', read_only=True)
    full_text_type = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = FullText
        fields = ['id', 'full_text_type', 'full_text_status', 'file', 'url', 'publication', 'first_created']
