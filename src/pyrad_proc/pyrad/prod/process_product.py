"""
pyrad.prod.process_product
==========================

Functions for obtaining Pyrad products from the datasets

.. autosummary::
    :toctree: generated/

    generate_vol_products
    generate_sun_hits_products
    generate_timeseries_products
    generate_monitoring_products

"""

from copy import deepcopy
from warnings import warn

import numpy as np

import pyart

from ..io.io_aux import get_fieldname_pyart
from ..io.io_aux import get_save_dir, make_filename
from ..io.io_aux import generate_field_name_str

from ..io.read_data_other import get_sensor_data, read_timeseries
from ..io.read_data_other import read_sun_retrieval, read_monitoring_ts

from ..io.write_data import write_timeseries, write_monitoring_ts
from ..io.write_data import write_sun_hits, write_sun_retrieval

from ..graph.plots import plot_ppi, plot_rhi, plot_cappi, plot_bscope
from ..graph.plots import plot_timeseries, plot_timeseries_comp
from ..graph.plots import plot_quantiles, get_colobar_label, plot_sun_hits
from ..graph.plots import plot_sun_retrieval_ts, plot_histogram
from ..graph.plots import plot_histogram2, plot_density, plot_monitoring_ts
from ..graph.plots import get_field_name, get_colobar_label

from ..util.radar_utils import create_sun_hits_field
from ..util.radar_utils import create_sun_retrieval_field
from ..util.radar_utils import compute_histogram, compute_quantiles
from ..util.radar_utils import compute_quantiles_from_hist


def generate_sun_hits_products(dataset, prdcfg):
    """
    generates sun hits products

    Parameters
    ----------
    dataset : tuple
        radar object and sun hits dictionary

    prdcfg : dictionary of dictionaries
        product configuration dictionary of dictionaries

    Returns
    -------
    filename : str
        the name of the file created. None otherwise

    """
    if prdcfg['type'] == 'WRITE_SUN_HITS':
        if 'sun_hits' not in dataset:
            return None

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'info', prdcfg['dstype'], 'detected', ['csv'],
            timeinfo=prdcfg['timeinfo'], timeformat='%Y%m%d')

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        write_sun_hits(dataset['sun_hits'], fname[0])

        print('saved sun hits file: '+fname[0])

        return fname[0]

    elif prdcfg['type'] == 'PLOT_SUN_HITS':
        if 'sun_hits_final' not in dataset:
            return None

        field_name = get_fieldname_pyart(prdcfg['voltype'])

        if prdcfg['voltype'] not in dataset['sun_hits_final']:
            warn(
                ' Field type ' + prdcfg['voltype'] +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'detected', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], timeinfo=prdcfg['timeinfo'],
            timeformat='%Y%m%d')

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        field = create_sun_hits_field(
            dataset['sun_hits_final']['rad_el'],
            dataset['sun_hits_final']['rad_az'],
            dataset['sun_hits_final']['sun_el'],
            dataset['sun_hits_final']['sun_az'],
            dataset['sun_hits_final'][prdcfg['voltype']],
            prdcfg['sunhitsImageConfig'])

        if field is None:
            warn(
                'Unable to create field '+prdcfg['voltype'] +
                ' Skipping product ' + prdcfg['type'])
            return None

        plot_sun_hits(field, field_name, fname, prdcfg)

        print('saved figures: '+' '.join(fname))

        return savedir+fname

    elif prdcfg['type'] == 'WRITE_SUN_RETRIEVAL':
        if 'sun_retrieval' not in dataset:
            return None

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=None)

        fname = make_filename(
            'info', prdcfg['dstype'], 'retrieval', ['csv'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        write_sun_retrieval(dataset['sun_retrieval'], fname[0])

        print('saved sun retrieval file: '+fname[0])

        return fname[0]

    elif prdcfg['type'] == 'PLOT_SUN_RETRIEVAL':
        if 'sun_retrieval' not in dataset:
            return None

        field_name = get_fieldname_pyart(prdcfg['voltype'])
        par = None
        if field_name == 'sun_est_power_h':
            par = 'par_h'
        elif field_name == 'sun_est_power_v':
            par = 'par_v'
        elif field_name == 'sun_est_differential_reflectivity':
            par = 'par_zdr'

        if par not in dataset['sun_retrieval']:
            warn(
                ' Field type ' + prdcfg['voltype'] +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'retrieval', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], timeinfo=prdcfg['timeinfo'],
            timeformat='%Y%m%d')

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        if dataset['sun_retrieval'][par] is None:
            warn(
                ' Invalid retrieval parameters. Skipping product ' +
                prdcfg['type'])
            return None

        field = create_sun_retrieval_field(
            dataset['sun_retrieval'][par], prdcfg['sunhitsImageConfig'])

        if field is not None:
            plot_sun_hits(field, field_name, fname, prdcfg)

        print('saved figures: '+' '.join(fname))

        return fname

    elif prdcfg['type'] == 'PLOT_SUN_RETRIEVAL_TS':
        if 'sun_retrieval' not in dataset:
            return None

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdid'], timeinfo=None)

        fname = make_filename(
            'info', prdcfg['dstype'], 'retrieval', ['csv'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        sun_retrieval = read_sun_retrieval(fname[0])

        if sun_retrieval[0] is None:
            warn(
                'Unable to read sun retrieval file '+fname[0])
            return None

        if len(sun_retrieval[0]) < 2:
            warn(
                'Unable to plot sun retrieval time series. ' +
                'Not enough data points.')
            return None

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=None)

        fname = make_filename(
            'retrieval_ts', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        plot_sun_retrieval_ts(
            sun_retrieval, prdcfg['voltype'], fname)

        print('saved figures: '+' '.join(fname))

        return fname

    else:
        if 'radar' in dataset:
            generate_vol_products(dataset['radar'], prdcfg)


def generate_vol_products(dataset, prdcfg):
    """
    generates radar volume products

    Parameters
    ----------
    dataset : Radar
        radar object

    prdcfg : dictionary of dictionaries
        product configuration dictionary of dictionaries

    Returns
    -------
    no return

    """
    if prdcfg['type'] == 'PPI_IMAGE':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        el_vec = np.sort(dataset.fixed_angle['data'])
        el = el_vec[prdcfg['anglenr']]
        ind_el = np.where(dataset.fixed_angle['data'] == el)[0][0]

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'ppi', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo='el'+'{:.1f}'.format(el),
            timeinfo=prdcfg['timeinfo'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        step = None
        quantiles = None
        plot_type = 'PPI'
        if 'plot_type' in prdcfg:
            plot_type = prdcfg['plot_type']
        if 'step' in prdcfg:
            step = prdcfg['step']
        if 'quantiles' in prdcfg:
            quantiles = prdcfg['quantiles']

        plot_ppi(dataset, field_name, ind_el, prdcfg, fname,
                 plot_type=plot_type, step=step, quantiles=quantiles)

        print('saved figures: '+' '.join(fname))

        return fname

    elif prdcfg['type'] == 'RHI_IMAGE':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        az_vec = np.sort(dataset.fixed_angle['data'])
        az = az_vec[prdcfg['anglenr']]
        ind_az = np.where(dataset.fixed_angle['data'] == az)[0][0]

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'rhi', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo='az'+'{:.1f}'.format(az),
            timeinfo=prdcfg['timeinfo'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        step = None
        quantiles = None
        plot_type = 'RHI'
        if 'plot_type' in prdcfg:
            plot_type = prdcfg['plot_type']
        if 'step' in prdcfg:
            step = prdcfg['step']
        if 'quantiles' in prdcfg:
            quantiles = prdcfg['quantiles']

        plot_rhi(dataset, field_name, ind_az, prdcfg, fname,
                 plot_type=plot_type, step=step, quantiles=quantiles)

        print('saved figures: '+' '.join(fname))

        return fname

    elif prdcfg['type'] == 'PSEUDOPPI_IMAGE':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        try:
            xsect = pyart.util.cross_section_rhi(
                dataset, [prdcfg['angle']], el_tol=prdcfg['EleTol'])

            savedir = get_save_dir(
                prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
                prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

            fname = make_filename(
                'ppi', prdcfg['dstype'], prdcfg['voltype'],
                prdcfg['imgformat'],
                prdcfginfo='el'+'{:.1f}'.format(prdcfg['angle']),
                timeinfo=prdcfg['timeinfo'])

            for i in range(len(fname)):
                fname[i] = savedir+fname[i]

            step = None
            quantiles = None
            plot_type = 'PPI'
            if 'plot_type' in prdcfg:
                plot_type = prdcfg['plot_type']
            if 'step' in prdcfg:
                step = prdcfg['step']
            if 'quantiles' in prdcfg:
                quantiles = prdcfg['quantiles']

            plot_ppi(xsect, field_name, 0, prdcfg, fname,
                     plot_type=plot_type, step=step, quantiles=quantiles)

            print('saved figures: '+' '.join(fname))

            return fname
        except EnvironmentError:
            warn(
                'No data found at elevation ' + str(prdcfg['angle']) +
                '. Skipping product ' + prdcfg['type'])

            return None

    elif prdcfg['type'] == 'PSEUDORHI_IMAGE':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        try:
            xsect = pyart.util.cross_section_ppi(
                dataset, [prdcfg['angle']], az_tol=prdcfg['AziTol'])

            savedir = get_save_dir(
                prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
                prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

            fname = make_filename(
                'rhi', prdcfg['dstype'], prdcfg['voltype'],
                prdcfg['imgformat'],
                prdcfginfo='az'+'{:.1f}'.format(prdcfg['angle']),
                timeinfo=prdcfg['timeinfo'])

            for i in range(len(fname)):
                fname[i] = savedir+fname[i]

            step = None
            quantiles = None
            plot_type = 'RHI'
            if 'plot_type' in prdcfg:
                plot_type = prdcfg['plot_type']
            if 'step' in prdcfg:
                step = prdcfg['step']
            if 'quantiles' in prdcfg:
                quantiles = prdcfg['quantiles']

            plot_rhi(xsect, field_name, 0, prdcfg, fname,
                     plot_type=plot_type, step=step, quantiles=quantiles)

            print('saved figures: '+' '.join(fname))

            return fname
        except EnvironmentError:
            warn(
                ' No data found at azimuth ' +
                str(prdcfg['angle'])+'. Skipping product ' +
                prdcfg['type'])
            return None

    elif prdcfg['type'] == 'CAPPI_IMAGE':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'cappi', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'],
            prdcfginfo='alt'+'{:.1f}'.format(prdcfg['altitude']),
            timeinfo=prdcfg['timeinfo'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        plot_cappi(dataset, field_name, prdcfg['altitude'], prdcfg, fname)
        print('saved figures: '+' '.join(fname))

        return fname

    if prdcfg['type'] == 'BSCOPE_IMAGE':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        ang_vec = np.sort(dataset.fixed_angle['data'])
        ang = ang_vec[prdcfg['anglenr']]
        ind_ang = np.where(dataset.fixed_angle['data'] == ang)[0][0]

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'b-scope', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'],
            prdcfginfo='ang'+'{:.1f}'.format(ang),
            timeinfo=prdcfg['timeinfo'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        plot_bscope(dataset, field_name, ind_ang, prdcfg, fname)
        print('saved figures: '+' '.join(fname))

        return fname

    if prdcfg['type'] == 'HISTOGRAM':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        step = None
        if 'step' in prdcfg:
            step = prdcfg['step']

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'histogram', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'],
            timeinfo=prdcfg['timeinfo'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        bins, values = compute_histogram(
            dataset.fields[field_name]['data'], field_name, step=step)

        titl = (
            pyart.graph.common.generate_radar_time_begin(
                dataset).isoformat() + 'Z' + '\n' +
            get_field_name(dataset.fields[field_name], field_name))

        labelx = get_colobar_label(dataset.fields[field_name], field_name)

        plot_histogram(bins, values, fname, labelx=labelx,
                       labely='Number of Samples', titl=titl)

        print('saved figures: '+' '.join(fname))

        return fname

    if prdcfg['type'] == 'QUANTILES':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        quantiles = None
        if 'quantiles' in prdcfg:
            quantiles = prdcfg['quantiles']

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'quantiles', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'],
            timeinfo=prdcfg['timeinfo'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        quantiles, values = compute_quantiles(
            dataset.fields[field_name]['data'], quantiles=quantiles)

        titl = (
            pyart.graph.common.generate_radar_time_begin(
                dataset).isoformat() + 'Z' + '\n' +
            get_field_name(dataset.fields[field_name], field_name))

        labely = get_colobar_label(dataset.fields[field_name], field_name)

        plot_quantiles(quantiles, values, fname, labelx='quantile',
                       labely=labely, titl=titl)

        print('saved figures: '+' '.join(fname))

        return fname

    elif prdcfg['type'] == 'SAVEVOL':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        new_dataset = deepcopy(dataset)
        new_dataset.fields = dict()
        new_dataset.add_field(field_name, dataset.fields[field_name])

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'savevol', prdcfg['dstype'], prdcfg['voltype'], ['nc'],
            timeinfo=prdcfg['timeinfo'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        pyart.io.cfradial.write_cfradial(fname[0], new_dataset)
        print('saved file: '+fname[0])

        return fname[0]

    elif prdcfg['type'] == 'SAVEALL':
        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'savevol', prdcfg['dstype'], 'all_fields', ['nc'],
            timeinfo=prdcfg['timeinfo'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        pyart.io.cfradial.write_cfradial(fname[0], dataset)
        print('saved file: '+fname[0])

        return fname[0]

    else:
        warn(' Unsupported product type: ' + prdcfg['type'])
        return None


def generate_timeseries_products(dataset, prdcfg):
    """
    generates time series products

    Parameters
    ----------
    dataset : dictionary
        radar object

    prdcfg : dictionary of dictionaries
        product configuration dictionary of dictionaries

    Returns
    -------
    no return

    """
    if prdcfg['type'] == 'PLOT_AND_WRITE_POINT':
        az = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][0])
        el = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][1])
        r = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][2])
        gateinfo = ('az'+az+'r'+r+'el'+el)

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        csvfname = make_filename(
            'ts', prdcfg['dstype'], dataset['datatype'], ['csv'],
            prdcfginfo=gateinfo, timeinfo=prdcfg['timeinfo'],
            timeformat='%Y%m%d')

        for i in range(len(csvfname)):
            csvfname[i] = savedir+csvfname[i]

        write_timeseries(dataset, csvfname[0])
        print('saved CSV file: '+csvfname[0])

        date, value = read_timeseries(csvfname[0])

        if date is None:
            warn(
                'Unable to plot time series. No valid data')
            return None

        figfname = make_filename(
            'ts', prdcfg['dstype'], dataset['datatype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=date[0], timeformat='%Y%m%d')

        for i in range(len(figfname)):
            figfname[i] = savedir+figfname[i]

        label1 = 'Radar (az, el, r): ('+az+', '+el+', '+r+')'
        titl = ('Time Series '+date[0].strftime('%Y-%m-%d'))

        labely = generate_field_name_str(dataset['datatype'])

        plot_timeseries(
            date, value, figfname, labelx='Time UTC',
            labely=labely, label1=label1, titl=titl)
        print('saved figures: '+' '.join(figfname))

        return savedir+figfname

    elif prdcfg['type'] == 'PLOT_CUMULATIVE_POINT':
        az = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][0])
        el = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][1])
        r = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][2])
        gateinfo = ('az'+az+'r'+r+'el'+el)

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdid'], timeinfo=prdcfg['timeinfo'])

        csvfname = make_filename(
            'ts', prdcfg['dstype'], dataset['datatype'], ['csv'],
            prdcfginfo=gateinfo, timeinfo=prdcfg['timeinfo'],
            timeformat='%Y%m%d')

        for i in range(len(csvfname)):
            csvfname[i] = savedir+csvfname[i]

        date, value = read_timeseries(csvfname[0])

        if date is None:
            warn(
                'Unable to plot accumulationtime series. No valid data')
            return None

        figfname = make_filename(
            'ts_cum', prdcfg['dstype'], dataset['datatype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=date[0], timeformat='%Y%m%d')

        for i in range(len(figfname)):
            figfname[i] = savedir+figfname[i]

        label1 = 'Radar (az, el, r): ('+az+', '+el+', '+r+')'
        titl = ('Time Series Acc. '+date[0].strftime('%Y-%m-%d'))

        labely = 'Radar estimated rainfall accumulation (mm)'

        plot_timeseries(
            date, value, figfname, labelx='Time UTC',
            labely=labely, label1=label1, titl=titl,
            period=prdcfg['ScanPeriod']*60.)
        print('saved figures: '+' '.join(figfname))

        return figfname

    elif prdcfg['type'] == 'COMPARE_POINT':
        az = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][0])
        el = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][1])
        r = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][2])
        gateinfo = ('az'+az+'r'+r+'el'+el)

        savedir_ts = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdid'], timeinfo=prdcfg['timeinfo'])

        csvfname = make_filename(
            'ts', prdcfg['dstype'], dataset['datatype'], ['csv'],
            prdcfginfo=gateinfo, timeinfo=prdcfg['timeinfo'],
            timeformat='%Y%m%d')

        for i in range(len(csvfname)):
            csvfname[i] = savedir_ts+csvfname[i]

        radardate, radarvalue = read_timeseries(csvfname[0])
        if radardate is None:
            warn(
                'Unable to plot sensor comparison at point of interest. ' +
                'No valid radar data')
            return None

        sensordate, sensorvalue, sensortype, period = get_sensor_data(
            radardate[0], dataset['datatype'], prdcfg)
        if sensordate is None:
            warn(
                'Unable to plot sensor comparison at point of interest. ' +
                'No valid sensor data')
            return None

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=radardate[0])

        figfname = make_filename(
            'ts_comp', prdcfg['dstype'], dataset['datatype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=radardate[0], timeformat='%Y%m%d')

        for i in range(len(figfname)):
            figfname[i] = savedir+figfname[i]

        label1 = 'Radar (az, el, r): ('+az+', '+el+', '+r+')'
        label2 = sensortype+' '+prdcfg['sensorid']
        titl = 'Time Series Comp. '+radardate[0].strftime('%Y-%m-%d')
        labely = generate_field_name_str(dataset['datatype'])

        plot_timeseries_comp(
            radardate, radarvalue, sensordate, sensorvalue, figfname,
            labelx='Time UTC', labely=labely, label1=label1, label2=label2,
            titl=titl)
        print('saved figures: '+' '.join(figfname))

        return figfname

    elif prdcfg['type'] == 'COMPARE_CUMULATIVE_POINT':
        az = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][0])
        el = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][1])
        r = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][2])
        gateinfo = ('az'+az+'r'+r+'el'+el)

        savedir_ts = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['timeinfo'],
            prdcfg['dsname'], prdcfg['prdid'])

        csvfname = make_filename(
            'ts', prdcfg['dstype'], dataset['datatype'], ['csv'],
            prdcfginfo=gateinfo, timeinfo=prdcfg['timeinfo'],
            timeformat='%Y%m%d')

        for i in range(len(csvfname)):
            csvfname[i] = savedir_ts+csvfname[i]

        radardate, radarvalue = read_timeseries(csvfname[0])
        if radardate is None:
            warn(
                'Unable to plot sensor comparison at point of interest. ' +
                'No valid radar data')
            return None

        sensordate, sensorvalue, sensortype, period2 = get_sensor_data(
            radardate[0], dataset['datatype'], prdcfg)
        if sensordate is None:
            warn(
                'Unable to plot sensor comparison at point of interest. ' +
                'No valid sensor data')
            return None

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=radardate[0])

        figfname = make_filename(
            'ts_cumcomp', prdcfg['dstype'], dataset['datatype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=radardate[0], timeformat='%Y%m%d')

        for i in range(len(figfname)):
            figfname[i] = savedir+figfname[i]

        label1 = 'Radar (az, el, r): ('+az+', '+el+', '+r+')'
        label2 = sensortype+' '+prdcfg['sensorid']
        titl = ('Time Series Acc. Comp. ' +
                radardate[0].strftime('%Y-%m-%d'))
        labely = 'Rainfall accumulation (mm)'

        plot_timeseries_comp(
            radardate, radarvalue, sensordate, sensorvalue,
            figfname, labelx='Time UTC', labely=labely,
            label1=label1, label2=label2, titl=titl,
            period1=prdcfg['ScanPeriod']*60., period2=period2)
        print('saved figures: '+' '.join(figfname))

        return figfname

    else:
        warn(' Unsupported product type: ' + prdcfg['type'])
        return None


def generate_monitoring_products(dataset, prdcfg):

    # check the type of dataset required
    hist_type = 'cumulative'
    if 'hist_type' in prdcfg:
        hist_type = prdcfg['hist_type']

    if dataset['hist_type'] != hist_type:
        return None

    hist_obj = dataset['hist_obj']

    if prdcfg['type'] == 'VOL_HISTOGRAM':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in hist_obj.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        timeformat = '%Y%m%d'
        titl = (
                pyart.graph.common.generate_radar_time_begin(
                    hist_obj).strftime('%Y-%m-%d') + '\n' +
                get_field_name(hist_obj.fields[field_name], field_name))
        if hist_type == 'instant':
            timeformat = '%Y%m%d%H%M%S'
            titl = (
                pyart.graph.common.generate_radar_time_begin(
                    hist_obj).isoformat() + 'Z' + '\n' +
                get_field_name(hist_obj.fields[field_name], field_name))

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'histogram', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'],
            timeinfo=prdcfg['timeinfo'], timeformat=timeformat)

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        labelx = get_colobar_label(hist_obj.fields[field_name], field_name)

        plot_histogram2(
            hist_obj.range['data'],
            np.sum(hist_obj.fields[field_name]['data'], axis=0),
            fname, labelx=labelx, labely='Number of Samples',
            titl=titl)

        print('saved figures: '+' '.join(fname))

        return fname

    if prdcfg['type'] == 'PPI_HISTOGRAM':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in hist_obj.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        el_vec = np.sort(hist_obj.fixed_angle['data'])
        el = el_vec[prdcfg['anglenr']]
        ind_el = np.where(hist_obj.fixed_angle['data'] == el)[0][0]

        timeformat = '%Y%m%d'
        titl = (
                '{:.1f}'.format(el)+' Deg. ' +
                pyart.graph.common.generate_radar_time_begin(
                    hist_obj).strftime('%Y-%m-%d') + '\n' +
                get_field_name(hist_obj.fields[field_name], field_name))
        if hist_type == 'instant':
            timeformat = '%Y%m%d%H%M%S'
            titl = (
                '{:.1f}'.format(el)+' Deg. ' +
                pyart.graph.common.generate_radar_time_begin(
                    hist_obj).isoformat() + 'Z' + '\n' +
                get_field_name(hist_obj.fields[field_name], field_name))

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'ppi', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo='el'+'{:.1f}'.format(el),
            timeinfo=prdcfg['timeinfo'], timeformat=timeformat)

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        labelx = get_colobar_label(hist_obj.fields[field_name], field_name)

        sweep_start = hist_obj.sweep_start_ray_index['data'][ind_el]
        sweep_end = hist_obj.sweep_end_ray_index['data'][ind_el]
        values = hist_obj.fields[field_name]['data'][sweep_start:sweep_end, :]
        plot_histogram2(
            hist_obj.range['data'], np.sum(values, axis=0),
            fname, labelx=labelx, labely='Number of Samples',
            titl=titl)

        print('saved figures: '+' '.join(fname))

        return fname

    if prdcfg['type'] == 'ANGULAR_DENSITY':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in hist_obj.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        el_vec = np.sort(hist_obj.fixed_angle['data'])
        el = el_vec[prdcfg['anglenr']]
        ind_el = np.where(hist_obj.fixed_angle['data'] == el)[0][0]

        timeformat = '%Y%m%d'
        if hist_type == 'instant':
            timeformat = '%Y%m%d%H%M%S'

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'ppi', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo='el'+'{:.1f}'.format(el),
            timeinfo=prdcfg['timeinfo'], timeformat=timeformat)

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        quantiles = np.array([25., 50., 75.])
        ref_value = 0.
        if 'quantiles' in prdcfg:
            quantiles = prdcfg['quantiles']
        if 'ref_value' in prdcfg:
            ref_value = prdcfg['ref_value']

        plot_density(
            hist_obj, hist_type, field_name, ind_el, prdcfg, fname,
            quantiles=quantiles, ref_value=ref_value)

        print('saved figures: '+' '.join(fname))

        return fname

    elif prdcfg['type'] == 'VOL_TS':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in hist_obj.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        csvtimeinfo = None
        if hist_type == 'instant':
            csvtimeinfo = prdcfg['timeinfo']

        quantiles = np.array([25., 50., 75.])
        ref_value = 0.
        if 'quantiles' in prdcfg:
            quantiles = prdcfg['quantiles']
        if 'ref_value' in prdcfg:
            ref_value = prdcfg['ref_value']

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=csvtimeinfo)

        csvfname = make_filename(
            'ts', prdcfg['dstype'], prdcfg['voltype'], ['csv'],
            timeinfo=csvtimeinfo, timeformat='%Y%m%d')

        for i in range(len(csvfname)):
            csvfname[i] = savedir+csvfname[i]

        quantiles, values = compute_quantiles_from_hist(
            hist_obj.range['data'],
            np.ma.sum(hist_obj.fields[field_name]['data'], axis=0),
            quantiles=quantiles)

        start_time = pyart.graph.common.generate_radar_time_begin(hist_obj)
        np_t = np.ma.sum(hist_obj.fields[field_name]['data'], dtype=int)
        if np.ma.getmaskarray(np_t):
            np_t = 0

        write_monitoring_ts(
            start_time, np_t, values, quantiles, prdcfg['voltype'],
            csvfname[0])
        print('saved CSV file: '+csvfname[0])

        date, np_t_vec, cquant_vec, lquant_vec, hquant_vec = (
            read_monitoring_ts(csvfname[0]))

        if date is None:
            warn(
                'Unable to plot time series. No valid data')
            return None

        figtimeinfo = None
        titldate = ''
        if hist_type == 'instant':
            figtimeinfo = date[0]
            titldate = date[0].strftime('%Y-%m-%d')

        figfname = make_filename(
            'ts', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'],
            timeinfo=figtimeinfo, timeformat='%Y%m%d')

        for i in range(len(figfname)):
            figfname[i] = savedir+figfname[i]

        titl = ('Monitoring Time Series '+titldate)

        labely = generate_field_name_str(prdcfg['voltype'])

        plot_monitoring_ts(
            date, np_t_vec, cquant_vec, lquant_vec, hquant_vec, field_name,
            figfname, ref_value=ref_value, labelx='Time UTC',
            labely=labely, titl=titl)
        print('saved figures: '+' '.join(figfname))

        return figfname

    elif prdcfg['type'] == 'SAVEVOL':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in hist_obj.fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        new_dataset = deepcopy(hist_obj)
        new_dataset.fields = dict()
        new_dataset.add_field(field_name, hist_obj.fields[field_name])

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], prdcfg['dsname'],
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname = make_filename(
            'savevol', prdcfg['dstype'], prdcfg['voltype'], ['nc'],
            timeinfo=prdcfg['timeinfo'])

        for i in range(len(fname)):
            fname[i] = savedir+fname[i]

        pyart.io.cfradial.write_cfradial(fname[0], new_dataset)
        print('saved file: '+fname[0])

        return fname[0]

    else:
        warn(' Unsupported product type: ' + prdcfg['type'])
        return None
