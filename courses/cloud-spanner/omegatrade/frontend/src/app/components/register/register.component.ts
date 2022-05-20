import { Component, OnInit, Optional } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ValidationService } from '../../services/validation.service';
import { RestService } from '../../services/rest.service';
import { SocialAuthService } from 'angularx-social-login';
import { GoogleLoginProvider } from 'angularx-social-login';
import { TokenStorageService } from '../../services/token-storage.service';
import { SnackBarService } from '../../services/snackbar.service';
import { take } from "rxjs/operators";
import { ChangePasswordComponent } from '../change-password/change-password.component';
import { MatDialog } from '@angular/material/dialog';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent implements OnInit {
  signUpForm: any;
  loader = false;
  user: any;
  enableOAuth:boolean = false;
  
  // tslint:disable-next-line: max-line-length
  constructor(private snackBarService: SnackBarService, private tokenStorage: TokenStorageService, private formBuilder: FormBuilder, private restService: RestService, private router: Router, @Optional() private authService: SocialAuthService,private dialog: MatDialog) {
    // Init sign-up form with form builder.
    this.signUpForm = this.formBuilder.group({
      fullName: ['', [Validators.required]],
      businessEmail: ['', [Validators.required, ValidationService.emailValidator]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required, Validators.minLength(6)]],
      provider: [''],
      photoUrl: ['']
    },{validators: ValidationService.checkPasswords.bind(this)});
    if(environment.clientId && environment.clientId!=""){
      this.enableOAuth=true;
    }
  }

  /**
   *  Function to Initiate component.
   */
  ngOnInit(): void {
  }

  /**
   * Function to sign-up with google provider
   */
  signUpWithGoogle(): void {
    this.authService.signIn(GoogleLoginProvider.PROVIDER_ID).then(user => {
      this.loader = true;
      this.restService.postData('users/google-sign-in', user)
        .pipe(take(1))
        .subscribe(
          response => {
            if (response && response.success) {
              this.tokenSuccessHandler(response);
              const forceChangePassword = response.userInfo.forceChangePassword;
              if (forceChangePassword === true) {
                this.changePassword({ ...response.userInfo, forceChangePassword })
              }
            }
            this.loader = false;
          },
          error => {
            this.snackBarService.openSnackBar(error.error.message, '');
            this.loader = false;
            if (error.error && error.error.redirect === 'sign-up') {
              this.router.navigateByUrl('/sign-up');
            }
          });
    });
  }

  /**
   * Function to Register user.
   * return {null}
   */
  signUp(): void {
    if (this.signUpForm.dirty && this.signUpForm.valid) {
      this.loader = true;
      this.restService.postData('users/register-user', this.signUpForm.value)
        .pipe(take(1))
        .subscribe(
          response => {
            if (response && response.success) {
              this.tokenSuccessHandler(response);
            }
            this.loader = false;
          },
          error => {
            this.snackBarService.openSnackBar(error.error.message, '');
            this.loader = false;
          });
    }
  }

  /**
   * Function to save user information and auth token.
   * @param  response contains user profile and auth token
   */
  tokenSuccessHandler(response): void {
    this.tokenStorage.saveToken(response.authToken);
    this.tokenStorage.saveUser(response.userInfo);
    this.router.navigateByUrl('/dashboard');
    this.snackBarService.openSnackBar(response.message, '');
  }

  /**
   * Function to open change password component.
   * 
   */
   changePassword(user){
    this.dialog.open(ChangePasswordComponent, {
      width: '400px',
      data: user,
      disableClose: true 
    });
  }

}
