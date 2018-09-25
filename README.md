# RWSLD
Rijkswaterstaat Linked Data Tools

## Scripts

* `mkschema` - extracts the DB's schema and generates a prototype ontology template
* `mkontology` - converts an ontology template to valid OWL
* `mkgraph` - convert a DB to knowledge graph using the supplied OWL ontology
* `mkextra` - enrich supplied knowledge graph with third-party data (eg, geo)
* `mkxrefs` - generate cross references between supplied knowledge graphs
* `mkotl` - generate OTL references in supplied knowledge graph
* `mkmerger` - merge supplied knowledge graphs

Note that 
1. database schemas and dumps are property of Rijkswaterstaat and are not included
2. `mkschema` requires restricted Rijkswaterstaat UML diagrams in some cases
3. `mkgraph` requires an OWL ontology to function 

## Example

To generate a schema
```$ python mkschema.py --server "<username>:<password>@<host:port>/<database>/<user>" --output <database>.json --datatype_schema datatypes.json```

To convert a DB to knowledge graph
```$ python mkgraph.py --server "<username>:<password>@<host:port>/<database>/<user>" --area "<X0> <Y0> <X1> <Y1>" --datatype_schema <database>.json --output <database>.ttl```
