'use strict';
require('dotenv').config({ path: '.env' })
const database = require('./app/config/database.js');
const { Spanner } = require('@google-cloud/spanner');
const companiesTable = database.table('companies');
const simulationsTable = database.table('simulations');
const stocksTable = database.table('companyStocks');

async function insertData() {
    try {
        const [data] = await database.table('companies').read({ columns: ['companyName'], json: true });
        if (data && data.length > 0) {
            throw { code: 500, details: "Dump failed, Companies table already contains data!" }
        }
        const companies = require('./sample-data/companies.json');
        const simulations = require('./sample-data/simulations.json');
        const stocks = require('./sample-data/stocks.json');
        for (var i = 0; i < stocks.length; i++) {
            stocks[i]["date"] = Spanner.float(new Date(parseFloat(stocks[i]["date"])).getTime());
        }
        console.log('Inserting Companies...');
        await companiesTable.insert(companies);
        console.log('done')
        console.log('Inserting Simulations...');
        await simulationsTable.insert(simulations);
        console.log('done')
        console.log('Inserting Stocks...');
        await stocksTable.insert(stocks);
        console.log('done')
        console.log('Data Loaded successfully');
    } catch (err) {
        console.error('ERROR:', err.code);
        console.error('DETAIL:', err.details);
    }
}
insertData();

