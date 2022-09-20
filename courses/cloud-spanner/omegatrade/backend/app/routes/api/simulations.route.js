const router = require('express').Router();
const SimulationController = require('../../controller/simulation.controller');
const validateToken = require('../../middlewares/jwt-auth.middleware').validateToken;

router.get('/list', validateToken, SimulationController.getList);
router.post('/start',validateToken, SimulationController.startSimulation);
router.put('/update',validateToken, SimulationController.updateSimulation);
router.delete('/delete/:sId/:companyId',validateToken, SimulationController.deleteSimulation);

module.exports = router;

