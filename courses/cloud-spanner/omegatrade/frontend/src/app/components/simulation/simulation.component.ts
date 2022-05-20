import { Component, OnInit, ViewChild } from '@angular/core';
import { MatSort } from '@angular/material/sort';
import { MatPaginator } from '@angular/material/paginator';
import { MatTableDataSource } from '@angular/material/table';
import { SnackBarService } from '../../services/snackbar.service';
import { FormBuilder, Validators, FormGroupDirective } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDialogModel, ConfirmDialogComponent } from '../confirm-dialog/confirm-dialog.component';
import { RestService } from '../../services/rest.service';
import { take } from 'rxjs/operators';
import { Router } from '@angular/router';


@Component({
  selector: 'app-simulation',
  templateUrl: './simulation.component.html',
  styleUrls: ['./simulation.component.css']
})

export class SimulationComponent implements OnInit  {

  displayedColumns: string[] = ['companyName', 'companyShortCode', 'status', 'action'];
  dataSource: MatTableDataSource<SimuationData>;
  @ViewChild(MatPaginator, { static: true }) paginator: MatPaginator;
  @ViewChild(MatSort) sort: MatSort;
  @ViewChild('mySelect') mySelect;

  searchInput: String;
  companies: any;
  simulateForm: any;
  simulations: any;
  interval = [5, 10, 15];
  noOfRecords = [50, 100, 150, 200];
  loader: boolean = false;
  runningSimulation = 0;
  maxAllowedSimulation = 3;
  
  constructor(private snackBarService: SnackBarService, private restService: RestService, private formBuilder: FormBuilder, public dialog: MatDialog, private router: Router) {
  }

  /**
   *  Function to Initiate component.
   */
  ngOnInit(): void {
    this.getCompanies();
    this.simulateForm = this.formBuilder.group({
      companyId: ['', []],
      timeInterval: ['', []],
      data: ['', []],
    },);
  }
  
  /**
   * Initalize and upates simulation table sort and pagination.
   */
  initializeSortAndPagination() {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  /**
   *  Function to get companies lists,
   *  and call simulation lists.
   */
  getCompanies() {
    this.restService.getData('companies/list')
      .pipe(take(1))
      .subscribe(
        response => {
          if (response && response.success) {
            this.companies = response.data;
            this.getSimulations();
          }
        },
        error => {
          if (error && error.error && error.error.message) {
            this.snackBarService.openSnackBar(error.error.message, '');
          }
        });
  }

  /**
   * Function to delete simulation.
   * @param simulation contains company's simulation.
   */
  deleteSimulation(simulation) {
    if (simulation && simulation.sId && simulation.companyName) {
      const dialogData = new ConfirmDialogModel("Confirm Action", `Are you sure you want to delete the simulation for ${simulation.companyName}?`);
      const dialogRef = this.dialog.open(ConfirmDialogComponent, {
        maxWidth: "400px",
        data: dialogData
      });
      dialogRef.afterClosed().pipe(take(1)).subscribe(dialogResult => {
        if (dialogResult === true) {
          this.restService.deleteData(`simulations/delete/${simulation.sId}/${simulation.companyId}`)
            .pipe(take(1))
            .subscribe(
              response => {
                if (response && response.success) {
                  this.snackBarService.openSnackBar(response.message, '');
                  const index = this.dataSource.data.findIndex(simulationObj => simulationObj.sId === simulation.sId);
                  if (index > -1) {
                    this.dataSource.data.splice(index, 1)
                    this.dataSource = new MatTableDataSource(this.dataSource.data);
                    if (simulation.status != "COMPLETED") {
                      --this.runningSimulation;
                    }
                    this.initializeSortAndPagination();
                  }
                  this.updateCompanyStatus(simulation.companyId);
                }
                this.loader = false;
              }, error => {
                if (error && error.error && error.error.message) {
                  this.snackBarService.openSnackBar(error.error.message, '');
                }
                this.loader = false;
              }
            );
        }
      });
    }
  }

  /**
   * Function to start simulation. 
   *  
   */
  simulate(formDirective: FormGroupDirective) {
    if (this.runningSimulation >= this.maxAllowedSimulation) {
      this.snackBarService.openSnackBar(`Cannot simulate more than ${this.maxAllowedSimulation} simulations simultaneously`, '');
      return false;
    }
    if (this.simulateForm.get('companyId').value && this.simulateForm.get('timeInterval').value && this.simulateForm.get('data').value) {
      this.loader = true;
      this.restService.postData('simulations/start', this.simulateForm.value)
        .pipe(take(1))
        .subscribe(
          response => {
            if (response && response.success) {
              this.updateCompanyStatus(this.simulateForm.get('companyId').value, true);
              this.simulateForm.reset();
              formDirective.resetForm();
              this.getSimulations();
            }
            this.loader = false;
          },
          error => {
            if (error && error.error && error.error.message) {
              this.snackBarService.openSnackBar(error.error.message, '');
            }
            this.loader = false;
          });
    } else {
      this.snackBarService.openSnackBar(`please choose all required form fields to simulate.`, '');
    }
  }

  /**
   * Get simulation lists and form material table.
   * MatTableDataSource that accepts a simulation data array and includes native support of filtering, sorting (using MatSort),
   * and pagination (using MatPaginator).
   */
  getSimulations() {
    this.loader = true;
    this.restService.getData('simulations/list')
      .pipe(take(1))
      .subscribe(
        response => {
          if (response && response.success) {
            this.dataSource = new MatTableDataSource(response.data);
            this.initializeSortAndPagination();
            this.runningSimulation = 0;
            if (response.data && response.data.length > 0) {
              for (var i = 0; i < response.data.length; i++) {
                if (response.data[i]['status'] != 'COMPLETED') {
                  ++this.runningSimulation;
                }
                this.updateCompanyStatus(response.data[i].companyId, true)
              }
            }
          }
          this.loader = false;
        },
        error => {
          if (error && error.error && error.error.message) {
            this.snackBarService.openSnackBar(error.error.message, '');
          }
          this.loader = false;
        });
  }

  /**
   * Function to update simulation.
   * @param sId {string} unique simulation id
   * @param status  using three types of simulation status.
   * PROCESSING - simulation is running.
   * COMPLETED - simulation completed for particular company.
   */
  updateSimulation(sId, companyId, status) {
    this.loader = true;
    const payLoad = { sId: sId, companyId: companyId, status: status }
    this.restService.putData(`simulations/update`, payLoad)
      .pipe(take(1))
      .subscribe(
        response => {
          if (response && response.success) {
            this.getSimulations();
            this.snackBarService.openSnackBar(response.message, '');
          }
          this.loader = false;
        },
        error => {
          if (error && error.error && error.error.message) {
            this.snackBarService.openSnackBar(error.error.message, '');
          }
          this.loader = false;
        });

  }

  /**
   * Function to avoid duplicate company simulation.
   * Disable a company in selection box if simulaton already started 
   * and enables if simulation deleted.
   * @param id company id.
   * @param disableVal contains boolean
   */
  updateCompanyStatus(id: string, disableVal: boolean = false) {
    if (id) {
      const index = this.companies.findIndex(company => company.companyId === id);
      if (index > -1) {
        this.companies[index].disable = disableVal;
      }
    }
  }

  /**
   * Function to apply Filter on simulation datasource.
   */
  applyFilter() {
    this.dataSource.filter = this.searchInput.trim().toLowerCase();
  }

  checkCompany() {
    const companyCount = (this.companies && this.companies.length) ? this.companies.length : 0;
    if (companyCount == 0) {
      let message = `No company found, 
      please create a company first by clicking on Manage Company.`
      this.showAlertMessage(message)
    } else {
      let diabledCount = 0;
      this.companies.map((company) => {
        if (company.disable === true) {
          ++diabledCount;
        }
      });
      if (diabledCount == companyCount) {
        let message = `Simulations have already been created for all available companies.
         To create additional simulations, 
         please go to Manage Company and add more companies first.`
        this.showAlertMessage(message)
      }
    }
  }

  showAlertMessage(message) {
    const dialogData = new ConfirmDialogModel("Alert", message);
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      maxWidth: "400px",
      data: { ...dialogData, isActionMsg: true }
    });
    dialogRef.afterClosed().pipe(take(1)).subscribe(() => {
      this.mySelect.close();
    });
  }

}

export interface SimuationData {
  sId: string;
  companyName: string;
  companyShortCode: string;
  status: String;
  companyId: String;
}


