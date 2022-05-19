import { Component, OnInit, Optional } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, Validators } from '@angular/forms';
import { ValidationService } from '../../services/validation.service';
import { RestService } from '../../services/rest.service';
import { TokenStorageService } from '../../services/token-storage.service';
import { SocialAuthService } from 'angularx-social-login';
import { GoogleLoginProvider } from 'angularx-social-login';
import { SnackBarService } from '../../services/snackbar.service';
import { ChangePasswordComponent } from '../change-password/change-password.component';
import { MatDialog } from '@angular/material/dialog';
import { take } from "rxjs/operators";
import { environment } from 'src/environments/environment';


@Component({
    selector: 'app-login',
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
    loginForm: any;
    loader = false;
    enableOAuth:boolean = false;
    
    // tslint:disable-next-line: max-line-length
    constructor(private snackBarService: SnackBarService, private tokenStorage: TokenStorageService, @Optional() private authService: SocialAuthService, private restService: RestService, private formBuilder: FormBuilder, private router: Router, private dialog: MatDialog) {
        this.loginForm = this.formBuilder.group({
            businessEmail: ['', [Validators.required, ValidationService.emailValidator]],
            password: ['', [Validators.required]]
        });
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
     *  Function to Sign-in with GoogleLoginProvider.
     */
    signInWithGoogle(): void {
        this.authService.signIn(GoogleLoginProvider.PROVIDER_ID).then(user => {
            this.loader = true;
            this.restService.postData('users/google-sign-in', user)
                .pipe(take(1))
                .subscribe(
                    response => {
                        if (response && response.success) {
                            this.tokenSuccessHandler(response);
                            const forceChangePassword = response.userInfo.forceChangePassword;
                            if(forceChangePassword === true){
                                this.changePassword({...response.userInfo,forceChangePassword})
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
     * Function to validate and login the user.
     */
    login(): void {
        if (this.loginForm.dirty && this.loginForm.valid) {
            this.loader = true;
            this.restService.postData('users/login', this.loginForm.value)
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


