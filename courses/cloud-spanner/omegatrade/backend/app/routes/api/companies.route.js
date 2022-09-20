const router = require('express').Router();
const CompanyController = require('../../controller/company.controller');
const DashboardController = require('../../controller/dashboard.controller');
const validateToken = require('../../middlewares/jwt-auth.middleware').validateToken;

router.get('/list', validateToken, CompanyController.getList);
router.get('/dashboard/:companyId', validateToken, DashboardController.getStockData);
router.post('/create', validateToken, CompanyController.create);
router.delete('/delete/:companyId', validateToken, CompanyController.delete);
router.put('/update/:companyId', validateToken, CompanyController.update);
module.exports = router;

