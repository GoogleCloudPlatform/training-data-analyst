import { Component, OnInit, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { TokenStorageService } from '../../services/token-storage.service';
import { FormBuilder, Validators, FormGroup } from '@angular/forms';
import { RestService } from '../../services/rest.service';
import { SnackBarService } from '../../services/snackbar.service';
import { ValidationService } from '../../services/validation.service';
import { take } from "rxjs/operators";

@Component({
  selector: 'app-change-password',
  templateUrl: './change-password.component.html',
  styleUrls: ['./change-password.component.css']
})
export class ChangePasswordComponent implements OnInit {

  userForm: FormGroup;
  forceChangePassword:boolean = false;
  loader: boolean = false;
  
  constructor(private snackBarService: SnackBarService, private restService: RestService, private formBuilder: FormBuilder, private dialogRef: MatDialogRef<ChangePasswordComponent>, @Inject(MAT_DIALOG_DATA) public data: any,private tokenService : TokenStorageService) {
    this.userForm = this.formBuilder.group({
      userId: ['', []],
      businessEmail: ['', [Validators.required]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required, Validators.minLength(6)]],
    },{validators: ValidationService.checkPasswords.bind(this)});
    if (data && data.userId) {
      this.userForm.setValue({
        userId: data.userId,
        businessEmail: data.businessEmail,
        password: '',
        confirmPassword: '',
      });
      this.userForm.get('businessEmail').disable();
      this.forceChangePassword = data.forceChangePassword || false;
    }
  }

  ngOnInit(): void {
  }

  /**
   * Function to changePassword
   * 
   */
  submitForm() {
    this.restService.postData(`users/change-password`, this.userForm.value)
      .pipe(take(1))
      .subscribe(response => {
        if (response && response.success) {
          this.tokenService.saveUser(response.user);
          this.dialogRef.close(response);
          this.snackBarService.openSnackBar(response.message, '');
        }
        this.loader = false;
      }, error => {
        this.loader = false;
        if (error && error.error && error.error.message) {
          this.snackBarService.openSnackBar(error.error.message, '');
        }
      });
  }
}






