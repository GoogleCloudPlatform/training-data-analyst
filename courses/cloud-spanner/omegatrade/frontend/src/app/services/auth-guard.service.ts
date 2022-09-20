import { Injectable } from '@angular/core';
import { RestService } from './rest.service';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router, Route } from '@angular/router';
import { Observable } from 'rxjs';
import { TokenStorageService } from './token-storage.service';
@Injectable()

export class AuthGuardService implements CanActivate {

  constructor(private tokenService: TokenStorageService, private router: Router, private restService: RestService) { }

  canActivate(next: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean> | Promise<boolean> | boolean {
    const user = this.tokenService.getUser();
    const token = this.tokenService.getToken();
    if (user && token) {
      return true;
    }
    else {
      this.router.navigate(['']);
      return false;
    }
  }
}
