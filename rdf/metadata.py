#!/usr/bin/python3

from logging import getLogger
from datetime import datetime

from rdflib.term import URIRef, Literal
from rdflib.namespace import Namespace, DCTERMS, VOID, XSD, OWL
from rdf.operators import add_property, add_type


logger = getLogger(__name__)

def add_metadata(g, base_namespace, timestamp, database, is_ontology=False):
    logger.info("Adding meta-data")

    # update namespaces
    _update_namespaces(g.namespace_manager)

    ns = dict(g.namespace_manager.namespaces())
    base = URIRef(ns[base_namespace])

    # number of triples (excluding meta data)
    ntriples = Literal(len(g), datatype=URIRef(ns['xsd'] + 'nonNegativeInteger'))
    add_property(g, base, ntriples, URIRef(ns['void'] + 'triples'))

    # type
    if is_ontology:
        add_type(g, base, URIRef(ns['owl'] + 'Ontology'))
        descriptiontype = "ontology"
    else:
        add_type(g, base, URIRef(ns['void'] + 'Dataset'))
        descriptiontype = "dataset"

    # modified
    modified = Literal(datetime.fromtimestamp(timestamp).isoformat(), datatype=URIRef(ns['xsd'] + 'dateTime'))
    add_property(g, base, modified, URIRef(ns['dcterms'] + 'modified'))

    # creator/published
    creator = URIRef(ns['dbpr'] + 'Vrije_Universiteit_Amsterdam')
    add_property(g, base, creator, URIRef(ns['dcterms'] + 'creator'))
    add_property(g, base, creator, URIRef(ns['dcterms'] + 'publisher'))

    # rights holder
    rightsholder = URIRef(ns['dbpr'] + 'Rijkswaterstaat')
    add_property(g, base, rightsholder, URIRef(ns['dcterms'] + 'rightsHolder'))

    # language
    language = URIRef("http://id.loc.gov/vocabulary/iso639-1/nl")
    add_property(g, base, language, URIRef(ns['dcterms'] + 'language'))

    # title
    title_nl = Literal("Rijkswaterstaat Linked Data Pilot Project - {}".format(database.upper()), lang="nl")
    title_en = Literal("Rijkswaterstaat Linked Data Pilot Project - {}".format(database.upper()), lang="en")
    add_property(g, base, title_nl, URIRef(ns['dcterms'] + 'title'))
    add_property(g, base, title_en, URIRef(ns['dcterms'] + 'title'))

    # subject 
    asset_management = URIRef(ns['dbpr'] + 'Asset_management')
    add_property(g, base, asset_management, URIRef(ns['dcterms'] + 'subject'))

    # description
    description_nl = Literal("Een {} voor experimentele doeleinden ten ".format(descriptiontype)\
                             + "behoeve van Rijkswaterstaats Linked Data "\
                             + "pilot project.", lang="nl")
    description_en = Literal("An experimental {} for purposes of ".format(descriptiontype)\
                             + "Rijkswaterstaat's Linked Data pilot "\
                             + "project.", lang="en")
    add_property(g, base, description_nl, URIRef(ns['dcterms'] + 'description'))
    add_property(g, base, description_en, URIRef(ns['dcterms'] + 'description'))

def _update_namespaces(namespace_manager):
    """ Update Namespaces
    """

    namespace_manager.bind('dbpr', Namespace("http://dbpedia.org/resource/"))
    namespace_manager.bind('dcterms', Namespace(DCTERMS))
    namespace_manager.bind('owl', Namespace(OWL))
    namespace_manager.bind('void', Namespace(VOID))
    namespace_manager.bind('xsd', Namespace(XSD))
