import { Component, OnInit, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { FormBuilder, Validators } from '@angular/forms';
import { RestService } from '../../../services/rest.service';
import { SnackBarService } from '../../../services/snackbar.service';
import { take } from "rxjs/operators";

@Component({
  selector: 'app-update-company',
  templateUrl: './update-company.component.html',
  styleUrls: ['./update-company.component.css']
})
export class UpdateCompanyComponent implements OnInit {

  companyForm: any;
  loader: boolean = false;
  action:String = "Add Company";

  constructor(private snackBarService: SnackBarService, private restService: RestService, private formBuilder: FormBuilder, private dialogRef: MatDialogRef<UpdateCompanyComponent>, @Inject(MAT_DIALOG_DATA) public data: any) {
    // Init the company Form
    this.companyForm = this.formBuilder.group({
      companyId: ['', []],
      companyName: ['', [Validators.required,Validators.maxLength(30)]],
      companyShortCode: ['', [Validators.required,Validators.maxLength(15)]]
    });
    if (data && data.companyId) {
      this.companyForm.setValue({
        companyId: data.companyId,
        companyName: data.companyName,
        companyShortCode: data.companyShortCode
      });
      this.companyForm.get('companyShortCode').disable();
      this.action = `Edit Company ${data.companyName}`
    }
  }

  /**
   * Function to create or update the company
   * 
   */
  submitForm() {
    if (this.companyForm.dirty && this.companyForm.valid) {
      this.loader = true;
      const companyId = this.companyForm.get('companyId').value;
      const path = ( companyId != '') ? `update/${companyId}` : 'create';
      if(companyId){
        this.updateCompany(path);
      }else{
        this.createCompany(path);
      }
    }
  }

  /**
   * Function to create a company
   * 
   */
  createCompany(path){
    this.restService.postData(`companies/${path}`, this.companyForm.value)
        .pipe(take(1))
        .subscribe(response => {
          if (response && response.success) {
            this.dialogRef.close(response);
            this.snackBarService.openSnackBar(response.message, '');
          }
          this.loader = false;
        },error => {
            this.loader = false;
            if(error && error.error && error.error.message){
              this.snackBarService.openSnackBar(error.error.message, '');
            }
          });
  }

  /**
   * Function to update a company
   * 
   */
  updateCompany(path){
    this.restService.putData(`companies/${path}`, this.companyForm.value)
        .pipe(take(1))
        .subscribe(response => {
          if (response && response.success) {
            this.dialogRef.close(response);
            this.snackBarService.openSnackBar(response.message, '');
          }
          this.loader = false;
        },error => {
            this.loader = false;
            if(error && error.error && error.error.message){
              this.snackBarService.openSnackBar(error.error.message, '');
            }
          });
  }

  ngOnInit(): void {
  
  }

}
