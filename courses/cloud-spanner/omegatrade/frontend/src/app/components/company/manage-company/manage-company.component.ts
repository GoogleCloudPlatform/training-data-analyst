import { Component, ViewChild, OnInit } from '@angular/core';
import { MatSort } from '@angular/material/sort';
import { MatPaginator } from '@angular/material/paginator';
import { MatTableDataSource } from '@angular/material/table';
import { MatDialog } from '@angular/material/dialog';
import { UpdateCompanyComponent } from '../update-company/update-company.component';
import { ConfirmDialogModel ,  ConfirmDialogComponent } from '../../confirm-dialog/confirm-dialog.component';
import { RestService } from '../../../services/rest.service';
import { SnackBarService } from '../../../services/snackbar.service';
import { take } from "rxjs/operators";

@Component({
  selector: 'app-manage-company',
  templateUrl: './manage-company.component.html',
  styleUrls: ['./manage-company.component.css']
})

export class ManageCompanyComponent implements OnInit {
  displayedColumns: string[] = ['companyName', 'companyShortCode', 'action'];
  dataSource: MatTableDataSource<CompanyData>;
  @ViewChild(MatPaginator, { static: true }) paginator: MatPaginator;
  @ViewChild(MatSort) sort: MatSort;
  searchInput:String;
  loader: boolean = false;

  constructor(private snackBarService: SnackBarService, private restService: RestService, public dialog: MatDialog) {
  }

  /**
  *  Function to Initiate component.
  */
  ngOnInit(): void {
    this.getCompanies();
  }

  
  initDataSource() {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }
  
  /**
   * Function to get the company List.
   * 
   * return {null}
   */
  getCompanies() {
    this.loader = true;
    this.restService.getData('companies/list')
      .pipe(take(1))
      .subscribe(response => {
        if (response && response.success) {
          this.dataSource = new MatTableDataSource(response.data);
          this.initDataSource();
        }
        this.loader = false;
      },
        error => {
          this.loader = false;
          if(error && error.error && error.error.message){
            this.snackBarService.openSnackBar(error.error.message, '');
          }
        });
  }

  /**
   * Function to delete a company.
   * 
   * return {null}
   */
  deleteCompany(companyObj) {
    const dialogData = new ConfirmDialogModel("Confirm Action", `Are you sure you want to delete company ${companyObj.companyName}?`);
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      maxWidth: "400px",
      data: dialogData
    });
    dialogRef.afterClosed().pipe(take(1)).subscribe(dialogResult => {
      if (dialogResult === true) {
        this.loader = true;
        this.restService.deleteData(`companies/delete/${companyObj.companyId}`)
          .pipe(take(1))
          .subscribe(response => {
            if (response && response.success) {
              const index = this.dataSource.data.findIndex(company => company.companyId === companyObj.companyId);
              if (index > -1){
                this.dataSource.data.splice(index, 1);
                this.dataSource = new MatTableDataSource(this.dataSource.data);
                this.initDataSource();
              }
              this.snackBarService.openSnackBar(response.message, '');
            }
            this.loader = false;
          },
            error => {
              this.loader = false;
              if(error && error.error && error.error.message){
                this.snackBarService.openSnackBar(error.error.message, '');
              }
            });
      }
    });
  }

  /**
   * Function to open create/edit company dialog
   * @param row contains company object
   */
  openCompanyDialog(row = null): void {
    const dialogRef = this.dialog.open(UpdateCompanyComponent, {
      width: '400px',
      data: row
    });
    dialogRef.afterClosed().pipe(take(1)).subscribe(response => {
      if (response && response.success) {
        this.getCompanies()
      }
    });
  }

  /**
   * Function to filter the companies based on user input
   * 
   */
  applyFilter() {
    this.dataSource.filter = this.searchInput.trim().toLowerCase();
  }

}

export interface CompanyData {
  companyId: string;
  companyName: string;
  companyShortCode: string;
}
