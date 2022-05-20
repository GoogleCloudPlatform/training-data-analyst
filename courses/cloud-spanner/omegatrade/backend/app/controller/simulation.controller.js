'use strict';
const Simulation = require('../models/simulation.model')
const Company = require('../models/company.model')
const { v4: uuidv4 } = require('uuid');
const { spannerNumericVal, spannerNumericRandValBetween, generateRandomValue } = require('../helpers/stockdata.helper');
const fakeStockmarketgenerator = require('fake-stock-market-generator');
const { Spanner } = require('@google-cloud/spanner');
const logService = require('../helpers/logservice');


/**
 * Function to list all simulations.
 * 
 * @method GET
 */
exports.getList = async function (req, res) {
    try {
        const simulation = await Simulation.getAll();
        return res.status(200).json({ success: true, data: simulation });
    } catch (error) {
        logService.writeLog('simulation.controller.getList', error);
        return res.status(500).json({ success: false, message: "Something went wrong while fetching all simulations" });
    }
};

/**
 * Function to update simulation
 * 
 * @method PUT
 */
exports.updateSimulation = async function (req, res) {
    try {
        const body = req.body;
        if (body) {
            await Simulation.update(body)
            return res.status(200).json({ success: true, message: `Simulation ${body.status}` });
        } else {
            return res.status(422).json({ success: false, message: "Update failed, please check the data" });
        }
    } catch (error) {
        logService.writeLog('simulation.controller.updateSimulation', error);
        return res.status(500).json({ success: false, "message": "Something went wrong while updating simulation." });
    }
}

/**
 * Function to delete simulation
 * 
 * @method DELETE
 */
exports.deleteSimulation = async function (req, res) {
    try {
        const sId = req.params.sId;
        const companyId = req.params.companyId;
        if (sId && companyId) {
            await Simulation.deleteById(sId)
            await Company.deleteStockData(companyId);
            return res.status(200).json({ success: true, message: 'deleted successfully' });
        }
        else {
            return res.status(422).json({ success: false, message: "Deletion failed, please check the data" });
        }
    } catch (error) {
        logService.writeLog('simulation.controller.deleteSimulation', error);
        return res.status(500).json({ success: false, "message": "Something went wrong while deleting a company" });
    }
};

/**
 * Function to simulate stock data
 * 
 * @method POST
 */
exports.startSimulation = async function (req, res) {
    try {
        const body = req.body;
        const [result] = await Company.findById(body.companyId);
        if (result && result.length > 0) {
            const company = result[0];
            const interval = body.timeInterval * 1000;
            const stock = fakeStockmarketgenerator.generateStockData(body.data).priceData;
            const sId = await Simulation.create(company.companyId);
            let stockDataCount = 0;
            let intervalId = setInterval(async () => {
                // Generating RandomData to match with stock logic
                const randomValue = generateRandomValue(100, 110);
                const dayHigh = randomValue + generateRandomValue();
                const dayLow = randomValue - generateRandomValue();
                const price = stock[stockDataCount].price;
                const stockData = {
                    companyStockId: uuidv4(),
                    companyId: body.companyId,
                    date: Spanner.float(new Date().getTime()),
                    currentValue: (price && price > 0) ? spannerNumericVal(price) : spannerNumericVal(randomValue),
                    open: spannerNumericVal(randomValue),
                    dayHigh: spannerNumericVal(dayHigh),
                    dayLow: spannerNumericVal(dayLow),
                    close: spannerNumericRandValBetween(dayHigh, dayLow, 2),
                    volume: spannerNumericRandValBetween(2000, 4000),
                    timestamp: 'spanner.commit_timestamp()'
                };
                const [simulation] = await Simulation.findById(sId);

                // check the existance of simulation and status is PROCESSING
                if (!simulation) {
                    // clears the intervalled loop if simulation deleted 
                    clearInterval(intervalId)
                } else if (simulation && simulation.sId) {
                    if (simulation.status === 'PROCESSING') {
                        await Company.createStockData(stockData);
                        // clears the interval when stockDataCount reaches value given in data.
                        if (stockDataCount === (body.data - 1)) {
                            // update completed status
                            await Simulation.update({ sId: sId, companyId: body.companyId, status: 'COMPLETED' })
                            clearInterval(intervalId)
                        }
                        stockDataCount++;
                    }
                }
            }, interval);
            return res.status(200).json({ success: true, sId: sId, message: "Simulation started." });
        } else {
            return res.status(422).json({ success: false, message: "Simulation failed, please check that the data you entered are valid." });
        }
    } catch (error) {
        logService.writeLog('simulation.controller.startSimulation', error);
        return res.status(500).json({ success: false, "message": "Something went wrong while starting the simulation." });
    }
}


