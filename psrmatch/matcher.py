# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Match sources to known source catalogues.
#

import logging
import os.path

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

        # tree lookup parameters
        self.max_neighbors = 25


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
        """

        if catalogue_name not in self.supported_catalogues:
            raise NotImplementedError('The catalogue is not supported: {0}'.format(catalogue_name))

        if catalogue_name == 'psrcat':
            catalogue = parse_psrcat(
                os.path.join(
                    os.path.dirname(__file__),
                    'catalogues',
                    'psrcat_v163.txt'
                )
            )

        self.catalogue = catalogue


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
        result: [~np.array, ~np.array]
            The distances and indices of the nearest neighbors.
        """

        result = self.tree.query(
            x=[source.ra.deg, source.dec.deg],
            p=2,
            k=self.max_neighbors,
            distance_upper_bound=self.dist_thresh
        )

        dist, idx  = result

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

        return result


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
