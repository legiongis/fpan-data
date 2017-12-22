#### Intro

This is an Arches v4 package (4.0.1) built for the FPAN HMS database. To install this package, please see the main project repo: [legiongis/fpan](https://github.com/legiongis/fpan).

#### What data is in here?

The HMS database is populated with exports from the [Florida Site Master File](dos.myflorida.com/historical/preservation/master-site-file/) (FMSF). Only three categories of resources from the FMSF are used:

- Archaeological Sites
- Historic Structures
- Historic Cemeteries
 
For the cemetery and archaeological sites, _all records_ from the FMSF are used. However, historic structures are filtered based on a few criteria. Only structures that
- are...
    - lighthouses
    - or located in...
        - State Parks
        - any NR district in St. Augustine
        - any NR district in Fernandino Beach
        - Pensacola Historic District or Palafox Historic District (both in Pensacola)
- and have not been demolished

All archaelogical site data is protected and not published in this repo, but for testing purposes a set of fake archaeological sites are included here.
    

