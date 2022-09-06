'use strict';
const Company = require('../models/company.model')
const logService = require('../helpers/logservice');
const { v4: uuidv4 } = require('uuid');
const Simulation = require('../models/simulation.model');

/**
 * Function to list all companies
 * @method GET
 */
exports.getList = async function (req, res) {
    try {
        const companies = await Company.getAll();
        return res.status(200).json({ success: true, data: companies });
    } catch (error) {
        logService.writeLog('company.controller.getList',error);
        return res.status(500).json({ success: false, message: 'Something went wrong while fetching all companies' });
    }
};

/**
 * Function to create company
 * @method POST
 * @param {JSON} req contains request headers and payload companyName,companyShortCode,companyId,created_at
 */
exports.create = async function (req, res) {
    try {
        const body = req.body;
        const [company] = await Company.checkCompany(body.companyName, body.companyShortCode);
        // check if  company is already added or not. 
        if (company && company.length > 0) {
            return res.status(409).json({ success: false, message: "Company already exists" });
        } else {
            body.companyId = uuidv4();
            body.created_at = 'spanner.commit_timestamp()';
            await Company.create(body);
            return res.status(200).json({ success: true, message: "Company created successfully" });
        }
    } catch (error) {
        logService.writeLog('company.controller.create',error);
        return res.status(500).json({ success: false, message: "Something went wrong while creating a new company." });
    }
};

/**
 * Function to update company
 * @method POST
 * @param {JSON} req contains request headers and payload companyName,companyShortCode,companyId,created_at and companyId
 */
exports.update = async function (req, res) {
    try {
        const body = req.body;
        const companyId = req.params.companyId
        if (body && companyId) {
            await Company.update(body)
            return res.status(200).json({ success: true, message: "Company details updated sucessfully!" });
        } else {
            res.status(422).json({
                success: false, message: `Something went wrong while updating a company,
                please check that the data you entered are valid.`
            });
        }
    } catch (error) {
        logService.writeLog('company.controller.update',error);
        return res.status(500).json({ success: false, message: "Something went wrong while updating a company." });
    }
}

/**
 * Function to Delete company
 * @method DELETE
 * @param {JSON} req contains request headers and request params companyId
 */
exports.delete = async function (req, res) {
    try {
        const companyId = req.params.companyId;
        const simulations = await Company.getCompanySimulation(companyId);
        if (simulations && simulations.length > 0) {
            return res.status(500).json({ success: false, message: `Deletion Failed, please delete the simulation of the company - ${simulations[0].companyName} first.` });
        } else {
            await Company.delete(companyId);
            return res.status(200).json({ success: true, message: "Company deleted!" });
        }
    } catch (error) {
        logService.writeLog('company.controller.delete', error);
        return res.status(500).json({ success: false, message: "Something went wrong while deleting a company." });
    }
};

