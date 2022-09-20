'use strict';
const Company = require('../models/company.model');
const logService = require('../helpers/logservice');

/**
 * Function to get stockdata of a company
 * @method GET
 * 
 * @param {\} req request headers and payload parameter of companyId and date.
 */
exports.getStockData = async function (req, res) {
    try {
        const companyId = req.params.companyId || null
        if (companyId) {
            const date = req.query.date ? parseFloat(req.query.date) : null;
            const [ company ] = await Company.getCompanySimulation(companyId);
            const stocks = await Company.getStocks(companyId, date);
            return res.status(200).json({ success: true, data: { company: company, stocks: stocks } });
        } else {
            return res.status(422).json({ success: false, message: 'Invalid data' });
        }
    } catch (error) {
        logService.log('dashboard.controller.getStockData',error);
        return res.status(500).json({ success: false, message: 'Something went wrong while fetching stock data lists.'  });
    }
};