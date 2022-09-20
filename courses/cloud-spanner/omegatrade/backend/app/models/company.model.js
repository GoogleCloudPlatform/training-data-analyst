'use strict';
const database = require('./../config/database.js');
const Company = function () { };

Company.getAll = async function () {
    const [companies] = await database.run({
        sql: `SELECT companyId , companyName , companyShortCode , created_at 
              FROM companies ORDER BY created_at DESC`,
        json: true,
    });
    return companies;
}

Company.create = async function (companyObj) {
    await database.table('companies').insert(companyObj);
    return companyObj.companyId
};

Company.checkCompany = async function (companyName, companyShortCode) {
    const company = await database.run({
        sql: `SELECT companyName , companyShortCode 
              FROM companies 
              WHERE companyName = @companyName OR companyShortCode = @companyShortCode 
              LIMIT 1`,
        params: {
            companyName: companyName,
            companyShortCode: companyShortCode
        },
        json: true
    });
    return company;
};

Company.delete = async function (companyId) {
    return await database.table('companies').deleteRows([companyId]);
}

Company.update = async function (companyObj) {
    return await database.table('companies').update([companyObj]);
}

Company.findById = async function (companyId) {
    return await database.run({
        sql: `SELECT companyId , companyName , companyShortCode , created_at  
              FROM companies 
              WHERE companyId = @companyId`,
        params: {
            companyId: companyId,
        },
        json: true
    });
}

Company.createStockData = async function (stockData) {
    return database.table('companyStocks').insert(stockData)
};

Company.deleteStockData = async function (companyId) {
    const [rowCount] = await database.runPartitionedUpdate({
        sql: 'DELETE FROM companyStocks WHERE companyId = @companyId',
        params: { companyId: companyId }
    });
    return rowCount;
}

Company.getCompanySimulation = async function (companyId) {
    const fields = `companies.companyId,companies.companyName,companies.companyShortCode,simulations.status,simulations.sId`
    const query = `SELECT ${fields}  
        FROM companies 
        INNER JOIN simulations ON companies.companyId = simulations.companyId
        WHERE companies.companyId = @companyId 
        ORDER BY simulations.createdAt DESC
        LIMIT 1`
    const [result] = await database.run({
        sql: query,
        params: { companyId: companyId },
        json: true
    });
    return result;
};

Company.getStocks = async function (companyId, date = null) {
    const conditions = ['companyId = @companyId'];
    const values = { companyId: companyId };
    if (date) {
        conditions.push('date > @date');
        values.date = date;
    }
    const [stockResult] = await database.run({
        sql: `SELECT date , currentValue 
                  FROM companyStocks  
                  WHERE  ${conditions.join(' AND ')}  
                  ORDER BY date`,
        params: values,
        json: true
    });
    return stockResult;
}

module.exports = Company