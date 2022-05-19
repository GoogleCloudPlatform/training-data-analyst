'use strict';
const database = require('./../config/database.js');
const { v4: uuidv4 } = require('uuid');
const Simulation = function () { };

Simulation.getAll = async function () {
    const [result] = await database.run({
        sql: `SELECT sml.sId as sId,sml.companyId as companyId, sml.status as status, cy.companyName as companyName, cy.companyShortCode as companyShortCode FROM simulations sml 
              INNER JOIN companies cy ON sml.companyId = cy.companyId 
              ORDER BY sml.createdAt DESC
              `,
        json: true
    });
    return result;
}

Simulation.findById = async function (sId) {
    const [result] = await database.run({
        sql: `SELECT sId,companyId,status 
        FROM simulations 
        WHERE sId = @sId`,
        params: {
            sId: sId
        },
        json: true
    });
    return result;
}

Simulation.create = async function (companyId) {
    const sId = uuidv4();
    await database.table('simulations').insert({
        sId: sId,
        status: 'PROCESSING',
        createdAt: 'spanner.commit_timestamp()',
        companyId: companyId,
    });
    return sId;
};

Simulation.deleteById = async function (sId) {
    return await database.table('simulations').deleteRows([sId]);
}

Simulation.update = async function (simulation) {
    return await database.table('simulations').update([simulation]);
}

module.exports = Simulation