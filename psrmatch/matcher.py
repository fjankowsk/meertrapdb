# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Match sources to known source catalogues.
#

import logging
import os.path

import numpy as np
from scipy.spatial import KDTree

from psrmatch.catalogue_helpers import parse_psrcat


class Matcher(object):
    """
    Match sources to catalogues of known sources.
    """

    # list of supported catalogues
    supported_catalogues = ['psrcat']

    def __init__(self, dist_thresh=1.5, dm_thresh=5.0):
        """
        Match sources to catalogues of known sources.

        Parameters
        ----------
        dist_thresh: float
            Distance threshold in degree.
        dm_thresh: float
            DM threshold in per cent.
        """

        self.dist_thresh = dist_thresh
        self.dm_thresh = dm_thresh / 100.0
        self.catalogue = None
        self.tree = None
        self.log = logging.getLogger('psrmatch.matcher')

        # list of loaded catalogues
        self.loaded_catalogues = []

        # tree lookup parameters
        self.max_neighbors = 25


    def get_loaded_catalogues(self):
        """
        Get the list of loaded catalogues.

        Returns
        -------
        loaded_catalogues: list of str
            The list of loaded catalogues.
        """

        return self.loaded_catalogues


    def get_supported_catalogues(self):
        """
        Get the list of supported catalogues.

        Returns
        -------
        supported_catalogues: list of str
            The list of supported catalogues.
        """

        return self.supported_catalogues


    def load_catalogue(self, catalogue_name):
        """
        Load a known-source catalogue.

        Parameters
        ----------
        catalogue_name: string
            The name of the catalogue to load.

        Raises
        ------
        NotImplementedError
            If the catalogue `catalogue_name` is not implemented.
        RuntimeError
            If the catalogue `catalogue_name` is already loaded.
        """

        if catalogue_name not in self.supported_catalogues:
            raise NotImplementedError('The catalogue is not supported: {0}'.format(catalogue_name))

        if catalogue_name in self.loaded_catalogues:
            raise RuntimeError('Catalogue is already loaded: {0}'.format(catalogue_name))

        if catalogue_name == 'psrcat':
            catalogue = parse_psrcat(
                os.path.join(
                    os.path.dirname(__file__),
                    'catalogues',
                    'psrcat_v164_beta.txt'
                )
            )

        self.catalogue = catalogue
        self.loaded_catalogues.append(catalogue_name)


    def unload_catalogues(self):
        """
        Unload all known-source catalogues.
        """

        self.catalogue = None
        self.loaded_catalogues = []
        self.tree = None


    def create_search_tree(self):
        """
        Create a k-d search tree from the catalogue.
        """

        self.tree = KDTree(
            list(zip(self.catalogue['ra'], self.catalogue['dec']))
        )


    def query_search_tree(self, source):
        """
        Query the search tree.

        Parameters
        ----------
        source: ~astropy.coordinates.SkyCoord
            The source to check.

        Returns
        -------
        dist, idx: (~np.array, ~np.array)
            The distances and indices of the nearest neighbors.
        """

        dist, idx = self.tree.query(
            x=[source.ra.deg, source.dec.deg],
            p=2,
            k=self.max_neighbors,
            distance_upper_bound=self.dist_thresh
        )

        # consider only those neighbors that are within the distance threshold
        # and remove the other neighbors
        mask = np.isfinite(dist)

        dist = dist[mask]
        idx = idx[mask]

        self.log.info('Nearest neighbors:')
        for d, i in zip(dist, idx):
            info_str = '{0:.3f}: {1:10} {2:17} {3:17} {4:.3f}'.format(
                d,
                self.catalogue[i]['psrj'],
                self.catalogue[i]['ra_str'],
                self.catalogue[i]['dec_str'],
                self.catalogue[i]['dm']
            )

            self.log.info(info_str)

        return dist, idx


    def find_matches(self, source, dm):
        """
        Find matches in spatial - DM space.

        Parameters
        ----------
        source: ~astropy.coordinates.SkyCoord
            The source to check.
        dm: float
            The dispersion measure of the source.
        """

        dist, idx  = self.query_search_tree(source)

        self.log.debug('Using distance threshold: {0} deg'.format(self.dist_thresh))
        self.log.debug('Using DM threshold: {0}'.format(self.dm_thresh))

        self.log.info('Source: {0}'.format(source.to_string('hmsdms')))

        match = None

        for d, i in zip(dist, idx):
            if d < self.dist_thresh \
            and abs(dm - self.catalogue[i]['dm']) / dm < self.dm_thresh:
                match = self.catalogue[i]
                self.log.info('Match found with distance: {0:.3f} deg'.format(d))
                break

        if match is None:
            self.log.info('No match found.')
        else:
            self.log.info('Found match: {0}, {1}, {2}, {3}'.format(
                match['psrj'],
                match['ra'],
                match['dec'],
                match['dm']
                )
            )

        return match
