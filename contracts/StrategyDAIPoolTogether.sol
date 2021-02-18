// SPDX-License-Identifier: MIT

pragma experimental ABIEncoderV2;
pragma solidity 0.6.12;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/math/Math.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import {BaseStrategy, StrategyParams} from "@yearnvaults/contracts/BaseStrategy.sol";

import "../../interfaces/poolTogether/IPoolTogether.sol";
import "../../interfaces/poolTogether/IPoolFaucet.sol";
import "../../interfaces/uniswap/Uni.sol";



contract StrategyDAIPoolTogether is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address public dai;
    address public wantPool;
    address public poolToken;
    address public unirouter;
    address public bonus;
    address public faucet;
    address public ticket;
    address public gov;
    string public constant override name = "StrategyDAIPoolTogether";

    // adding protection against slippage attacks
    //uint constant public DENOMINATOR = 10000;
    //uint public slip = 100;

    constructor(
        address _vault, // vault is v2, address is 0xBFa4D8AA6d8a379aBFe7793399D3DdaCC5bBECBB
        //address _want,
        address _wantPool,
        address _poolToken,
        address _unirouter,
        address _bonus,
        address _faucet,
        address _ticket,
        address _gov
    ) public BaseStrategy(_vault) {
        //want = _want;
        wantPool = _wantPool;
        poolToken = _poolToken;
        unirouter = _unirouter;
        bonus = _bonus;
        faucet = _faucet;
        ticket = _ticket;
        gov = _gov;

        IERC20(want).safeApprove(wantPool, uint256(-1));
        IERC20(poolToken).safeApprove(unirouter, uint256(-1));
        IERC20(bonus).safeApprove(unirouter, uint256(-1));
    }

    address public refer = 0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7;

    function protectedTokens() internal override view returns (address[] memory) {
        address[] memory protected = new address[](3);
        // (aka want) is already protected by default
        protected[0] = wantPool;
        protected[1] = poolToken;
        protected[2] = bonus;
        return protected;
    }


    // returns sum of all assets, realized and unrealized
    function estimatedTotalAssets() public override view returns (uint256) {
        //uint256 _bonusAmount = IERC20(bonus).balanceOf(address(this));
        uint256 reward = futureReward();
        uint256 poolProfit = futureProfit(reward, poolToken);
        return balanceOfWant().add(balanceOfPool()); // .add(poolProfit)
    }

    //todo: this
    function prepareReturn(uint256 _debtOutstanding) internal override returns (uint256 _profit, uint256 _loss, uint256 _debtPayment) {
       // We might need to return want to the vault
        if (_debtOutstanding > 0) {
           uint256 _amountFreed = 0;
           (_amountFreed, _loss) = liquidatePosition(_debtOutstanding);
           _debtPayment = Math.min(_amountFreed, _debtOutstanding);
        }

        //start by setting profit and loss to zero - will be changed later as needed
        _profit == 0;
        _loss == 0;

        // harvest() will track profit by estimated total assets compared to debt.
        uint256 balanceOfWantBefore = balanceOfWant();
        uint256 debt = vault.strategies(address(this)).totalDebt;


        uint256 currentValue = estimatedTotalAssets();

        if (currentValue > debt) {
            uint256 _amount = currentValue.sub(debt);
            (uint256 _liquidatedAmount,) = liquidatePosition(_amount);
            //_profit = _liquidatedAmount;
        }

        uint256 _gains = futureReward();
        if(_gains > 0) {
            claimReward();
        }

        uint256 _tokensAvailable = IERC20(poolToken).balanceOf(address(this));
        if(_tokensAvailable > 0) {
            _swap(_tokensAvailable, address(poolToken));
        }

        uint256 _bonusAvailable = IERC20(bonus).balanceOf(address(this));
        if(_bonusAvailable > 0) {
            _swap(_bonusAvailable, address(bonus));
        }

        uint256 balanceOfWantAfter = balanceOfWant();

        if(balanceOfWantAfter > balanceOfWantBefore) {
            _profit = balanceOfWantAfter.sub(balanceOfWantBefore);
        }

        if (debt > currentValue) {
            _loss = debt.sub(currentValue);
        }
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
       //emergency exit is dealt with in prepareReturn
        if (emergencyExit) {
          return;
       }

        // do not invest if we have more debt than want
        if (_debtOutstanding > balanceOfWant()) {
            return;
        }

       // Invest the rest of the want
       uint256 _wantAvailable = balanceOfWant().sub(_debtOutstanding);
        if (_wantAvailable > 0) {
            IPoolTogether(wantPool).depositTo(address(this), _wantAvailable, address(ticket), address(refer));
         }
    }

    //v0.3.0 - liquidatePosition is emergency exit. Supplants exitPosition
    function liquidatePosition(uint256 _amountNeeded) internal override returns (uint256 _liquidatedAmount, uint256 _loss) {
        if (balanceOfWant() < _amountNeeded) {
            // We need to withdraw to get back more want
            _withdrawSome(_amountNeeded.sub(balanceOfWant()));
        }

        uint256 balanceOfWant = balanceOfWant();

        if (balanceOfWant >= _amountNeeded) {
            _liquidatedAmount = _amountNeeded;
        } else {
            _liquidatedAmount = balanceOfWant;
            _loss = (_amountNeeded.sub(balanceOfWant));
        }
    }


    // withdraw some want from the vaults
    function _withdrawSome(uint256 _amount) internal returns (uint256) {
        uint256 balanceOfWantBefore = balanceOfWant();

        IPoolTogether(wantPool).withdrawInstantlyFrom(address(this), _amount, address(wantPool), 0);
        uint256 balanceAfter = balanceOfWant();
        return balanceAfter.sub(balanceOfWantBefore);
    }


    // transfers all tokens to new strategy
    function prepareMigration(address _newStrategy) internal override {
        // want is transferred by the base contract's migrate function
        IERC20(poolToken).transfer(_newStrategy, IERC20(poolToken).balanceOf(address(this)));
        IERC20(bonus).transfer(_newStrategy, IERC20(bonus).balanceOf(address(this)));
        IERC20(ticket).transfer(_newStrategy, IERC20(ticket).balanceOf(address(this)));
    }

    // returns value of total pool tickets
    function balanceOfPool() public view returns (uint256) {
        uint256 _balance = IERC20(wantPool).balanceOf(address(this));
        return (_balance);
    }

    // returns balance of want token
    function balanceOfWant() public view returns (uint256) {
        return want.balanceOf(address(this));
    }

    // calculates value of reward tokens into want
    function futureProfit(uint256 _amount, address _token) public view returns (uint256) {
        if (_amount == 0) {
            return 0;
        }

        address[] memory path = new address[](3);
        path[0] = address(_token); // token to convert
        path[1] = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2); // weth
        path[2] = address(want);
        uint256[] memory amounts = Uni(unirouter).getAmountsOut(_amount, path);

        return amounts[amounts.length - 1];

    }

    // swaps rewarded tokens for want
    function _swap(uint256 _amountIn, address _token) internal returns (uint256[] memory amounts) {
        address[] memory path = new address[](3);
        path[0] = address(_token); // token to swap
        path[1] = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2); // weth
        path[2] = address(want);

        Uni(unirouter).swapExactTokensForTokens(_amountIn, uint256(0), path, address(this), now);
    }

    // claims POOL from faucet
    function claimReward() internal returns (uint256) {
        uint256 poolBefore = IERC20(poolToken).balanceOf(address(this));
        IPoolFaucet(faucet).claim(address(this));
        uint256 poolAfter = IERC20(poolToken).balanceOf(address(this));
        if(poolAfter > poolBefore){
            uint256 claimed = poolAfter.sub(poolBefore);
            return claimed;
        } else{return 0;}
    }

    function setReferrer(address newReferral) external {
        refer = address(newReferral);
    }

    function futureReward() internal view returns (uint256) {
        uint256 lastExchangeRateMantissa;
        uint256 balance;
        IPoolFaucet(faucet).userStates(address(this));
        return balance;
    }

    ///function _sweepSwap(uint256 _amountIn, address _token) external onlyKeepers returns (uint256) {
    ///}

}

